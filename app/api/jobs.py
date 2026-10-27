import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.auth import require_api_key
from app.api.schemas import JobLocationUpdate, JobOut, Page
from app.database import get_db
from app.models import Job, User

router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(require_api_key)])

# Allowed ?sort= values. A leading "-" means descending. id is always the
# tie-breaker so paging is stable when many jobs share a date.
SORT_OPTIONS = {
    "date": (Job.job_date.asc(), Job.id.asc()),
    "-date": (Job.job_date.desc(), Job.id.desc()),
    "id": (Job.id.asc(),),
    "-id": (Job.id.desc(),),
}


def _get_job_or_404(db: Session, job_id: int) -> Job:
    job = db.query(Job).options(joinedload(Job.creator)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


@router.get("", response_model=Page[JobOut], summary="List jobs")
def list_jobs(
    username: Optional[str] = Query(None, description="Only jobs created by this username."),
    location: Optional[str] = Query(None, description="Location contains (case-insensitive)."),
    date_from: Optional[datetime.date] = Query(None, description="Job date on or after (YYYY-MM-DD)."),
    date_to: Optional[datetime.date] = Query(None, description="Job date on or before (YYYY-MM-DD)."),
    sort: Literal["-date", "date", "-id", "id"] = Query(
        "-date", description="Sort order: date / id ascending, -date / -id descending."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Newest job date first by default. Returns only id, location, date and the creating user."""
    query = db.query(Job)
    if username:
        query = query.join(Job.creator).filter(User.username == username.strip().lower())
    if location:
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))
    if date_from:
        query = query.filter(Job.job_date >= date_from)
    if date_to:
        query = query.filter(Job.job_date <= date_to)

    total = query.count()
    jobs = (
        query.options(joinedload(Job.creator))
        .order_by(*SORT_OPTIONS[sort])
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return Page(items=[JobOut.from_job(j) for j in jobs], total=total, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobOut, summary="Get a job by id")
def get_job(job_id: int, db: Session = Depends(get_db)):
    return JobOut.from_job(_get_job_or_404(db, job_id))


@router.patch("/{job_id}", response_model=JobOut, summary="Change a job's location")
def update_job_location(job_id: int, body: JobLocationUpdate, db: Session = Depends(get_db)):
    """Location is the only field the API can change."""
    job = _get_job_or_404(db, job_id)
    job.location = body.location
    db.commit()
    db.refresh(job)
    return JobOut.from_job(job)
