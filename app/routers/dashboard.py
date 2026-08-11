import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job
from app.choices import (
    CHECKLIST_FIELDS,
    DEVICE_TYPE_OPTIONS,
    COMPANY_NAME_OPTIONS,
    SERVICE_TYPE_TOP_OPTIONS,
    SERVICE_TYPE_INSPECTION_SUBOPTIONS,
    TEMPERING_OPTIONS,
    ROLE_VIEWER,
)
from app.dependencies import get_current_user, flash, get_flashed_messages
from app.render import templates

router = APIRouter()


def _parse_date(value: str) -> datetime.date:
    # value comes from <input type="date"> => "YYYY-MM-DD"
    return datetime.datetime.strptime(value, "%Y-%m-%d").date()


def _checklist_kwargs(form_data) -> dict:
    """Build a dict of {field_name: bool} from raw form data (checkboxes)."""
    return {name: (form_data.get(name) == "on") for name, _label in CHECKLIST_FIELDS}


def _service_type_value(form_data) -> str:
    """Combine the Service Type select + the Inspection sub-select into one
    stored value, e.g. 'Inspection - Tempering'."""
    top = (form_data.get("service_type_top") or "").strip()
    if top == "Inspection":
        sub = (form_data.get("service_type_sub") or "").strip()
        if sub:
            return f"Inspection - {sub}"
        return "Inspection"
    return top


def _tempering_value(form_data) -> str:
    """Multiple tampering-evidence checkboxes -> single comma separated string."""
    values = form_data.getlist("tempering")
    values = [v.strip() for v in values if v and v.strip()]
    return ", ".join(values)


def _selected_list(raw: str):
    if not raw:
        return []
    return [v.strip() for v in raw.split(",") if v.strip()]


@router.get("/dashboard")
async def dashboard_page(request: Request, q: str = "", db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    query = db.query(Job)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Job.vehicle_no.ilike(like),
                Job.device_id.ilike(like),
                Job.location.ilike(like),
            )
        )
    recent_jobs = query.order_by(Job.created_at.desc()).limit(20).all()
    total_jobs = db.query(Job).count()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "messages": get_flashed_messages(request),
            "jobs": recent_jobs,
            "total_jobs": total_jobs,
            "checklist_fields": CHECKLIST_FIELDS,
            "device_types": DEVICE_TYPE_OPTIONS,
            "company_names": COMPANY_NAME_OPTIONS,
            "service_type_top_options": SERVICE_TYPE_TOP_OPTIONS,
            "service_type_sub_options": SERVICE_TYPE_INSPECTION_SUBOPTIONS,
            "tempering_options": TEMPERING_OPTIONS,
            "q": q,
            "active_page": "dashboard",
            "today": datetime.date.today().isoformat(),
        },
    )


@router.post("/dashboard/jobs/create")
async def create_job(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user.role == ROLE_VIEWER:
        flash(request, "Viewers cannot create records.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    form = await request.form()

    vehicle_no = (form.get("vehicle_no") or "").strip()
    job_date_raw = form.get("job_date") or ""
    location = (form.get("location") or "").strip()

    if not vehicle_no or not job_date_raw or not location:
        flash(request, "Vehicle No., Date and Location are required.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    try:
        parsed_date = _parse_date(job_date_raw)
    except ValueError:
        flash(request, "Invalid date supplied.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    job = Job(
        vehicle_no=vehicle_no.upper(),
        device_id=(form.get("device_id") or "").strip() or None,
        company_name=(form.get("company_name") or "").strip() or None,
        job_date=parsed_date,
        location=location,
        before_images=(form.get("before_images") or "").strip() or None,
        after_images=(form.get("after_images") or "").strip() or None,
        service_form=(form.get("service_form") or "").strip() or None,
        po_number=(form.get("po_number") or "").strip() or None,
        device_type=(form.get("device_type") or "").strip() or None,
        service_type=_service_type_value(form) or None,
        tempering=_tempering_value(form) or None,
        tempering_evidence=(form.get("tempering_evidence") or "").strip() or None,
        notes=(form.get("notes") or "").strip() or None,
        created_by=user.id,
        **_checklist_kwargs(form),
    )
    db.add(job)
    db.commit()
    flash(request, f"Record for vehicle '{job.vehicle_no}' added successfully.", "success")
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/dashboard/jobs/{job_pk}/update")
async def update_job(request: Request, job_pk: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user.role == ROLE_VIEWER:
        flash(request, "Viewers cannot edit records.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    job = db.query(Job).filter(Job.id == job_pk).first()
    if not job:
        flash(request, "Record not found.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    form = await request.form()

    vehicle_no = (form.get("vehicle_no") or "").strip()
    job_date_raw = form.get("job_date") or ""
    location = (form.get("location") or "").strip()

    if not vehicle_no or not job_date_raw or not location:
        flash(request, "Vehicle No., Date and Location are required.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    try:
        parsed_date = _parse_date(job_date_raw)
    except ValueError:
        flash(request, "Invalid date supplied.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    job.vehicle_no = vehicle_no.upper()
    job.device_id = (form.get("device_id") or "").strip() or None
    job.company_name = (form.get("company_name") or "").strip() or None
    job.job_date = parsed_date
    job.location = location
    job.before_images = (form.get("before_images") or "").strip() or None
    job.after_images = (form.get("after_images") or "").strip() or None
    job.service_form = (form.get("service_form") or "").strip() or None
    job.po_number = (form.get("po_number") or "").strip() or None
    job.device_type = (form.get("device_type") or "").strip() or None
    job.service_type = _service_type_value(form) or None
    job.tempering = _tempering_value(form) or None
    job.tempering_evidence = (form.get("tempering_evidence") or "").strip() or None
    job.notes = (form.get("notes") or "").strip() or None

    for name, value in _checklist_kwargs(form).items():
        setattr(job, name, value)

    db.commit()
    flash(request, f"Record for vehicle '{job.vehicle_no}' updated successfully.", "success")
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/dashboard/jobs/{job_pk}/delete")
def delete_job(request: Request, job_pk: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if not user.is_admin_level:
        flash(request, "Only administrators can delete records.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    job = db.query(Job).filter(Job.id == job_pk).first()
    if not job:
        flash(request, "Record not found.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    vehicle_no = job.vehicle_no
    db.delete(job)
    db.commit()
    flash(request, f"Record for vehicle '{vehicle_no}' deleted.", "success")
    return RedirectResponse("/dashboard", status_code=303)
