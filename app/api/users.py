from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import require_api_key
from app.api.schemas import Page, UserCreate, UserOut, UserUpdate
from app.choices import ADMIN_LEVEL_ROLES
from app.database import get_db
from app.models import User
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_api_key)])


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.get("", response_model=Page[UserOut], summary="List users")
def list_users(
    q: Optional[str] = Query(None, description="Search username or full name (case-insensitive, partial match)."),
    role: Optional[str] = Query(None, description="Filter by role, e.g. user, field_support, viewer."),
    is_active: Optional[bool] = Query(None, description="Filter by active / deactivated accounts."),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(User.username.ilike(like), User.full_name.ilike(like)))
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    users = query.order_by(User.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return Page(items=[UserOut.from_user(u) for u in users], total=total, page=page, page_size=page_size)


@router.get("/by-username/{username}", response_model=UserOut, summary="Get a user by username")
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserOut.from_user(user)


@router.get("/{user_id}", response_model=UserOut, summary="Get a user by id")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return UserOut.from_user(_get_user_or_404(db, user_id))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create a user")
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    """Creates an approved, active account that can sign in to the web app immediately."""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Username '{body.username}' is already taken.")

    user = User(
        username=body.username,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role=body.role,
        is_active=True,
        is_approved=True,
        companies=", ".join(body.companies) or None,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Another request created the same username between the check and the insert.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Username '{body.username}' is already taken.")
    db.refresh(user)
    return UserOut.from_user(user)


@router.patch("/{user_id}", response_model=UserOut, summary="Update a user")
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db)):
    """Send only the fields you want to change. The username can't be changed."""
    user = _get_user_or_404(db, user_id)
    if user.role in ADMIN_LEVEL_ROLES:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Administrator accounts can only be managed from the Admin Panel.",
        )

    changes = body.model_dump(exclude_unset=True)
    for field in ("full_name", "role", "is_active"):
        if changes.get(field) is not None:
            setattr(user, field, changes[field])
    if changes.get("password") is not None:
        user.password_hash = hash_password(changes["password"])
    if "companies" in changes:
        user.companies = ", ".join(changes["companies"] or []) or None

    db.commit()
    db.refresh(user)
    return UserOut.from_user(user)
