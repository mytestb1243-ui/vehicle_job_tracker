from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import hash_password
from app.choices import ALL_ROLES, ROLE_USER, ROLE_SUPER_ADMIN, ADMIN_LEVEL_ROLES
from app.dependencies import get_current_user, flash, get_flashed_messages
from app.render import templates

router = APIRouter()

USERNAME_MAX_LEN = 80
FULL_NAME_MAX_LEN = 150


def _require_admin(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user:
        return None, RedirectResponse("/login", status_code=303)
    if not user.is_admin_level:
        flash(request, "You do not have permission to access the admin panel.", "error")
        return None, RedirectResponse("/dashboard", status_code=303)
    return user, None


def _active_admin_level_count(db: Session) -> int:
    return (
        db.query(User)
        .filter(User.role.in_(ADMIN_LEVEL_ROLES), User.is_active == True)  # noqa: E712
        .count()
    )


@router.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = _require_admin(request, db)
    if redirect:
        return redirect

    users = db.query(User).order_by(User.created_at.asc()).all()
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "user": user,
            "messages": get_flashed_messages(request),
            "users": users,
            "roles": ALL_ROLES,
            "active_page": "admin",
        },
    )


@router.post("/admin/users/create")
def create_user(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(""),
    password: str = Form(...),
    role: str = Form(ROLE_USER),
    db: Session = Depends(get_db),
):
    current_user, redirect = _require_admin(request, db)
    if redirect:
        return redirect

    if role == ROLE_SUPER_ADMIN and not current_user.is_super_admin:
        flash(request, "Only a Super Admin can create another Super Admin.", "error")
        return RedirectResponse("/admin", status_code=303)

    username_clean = username.strip().lower()
    full_name_clean = full_name.strip()
    if not username_clean or not password:
        flash(request, "Username and password are required.", "error")
        return RedirectResponse("/admin", status_code=303)

    if len(username_clean) > USERNAME_MAX_LEN:
        flash(request, f"Username is too long (max {USERNAME_MAX_LEN} characters).", "error")
        return RedirectResponse("/admin", status_code=303)

    if len(full_name_clean) > FULL_NAME_MAX_LEN:
        flash(request, f"Full name is too long (max {FULL_NAME_MAX_LEN} characters).", "error")
        return RedirectResponse("/admin", status_code=303)

    if len(password) < 6:
        flash(request, "Password must be at least 6 characters.", "error")
        return RedirectResponse("/admin", status_code=303)

    if role not in ALL_ROLES:
        role = ROLE_USER

    existing = db.query(User).filter(User.username == username_clean).first()
    if existing:
        flash(request, f"Username '{username_clean}' is already taken.", "error")
        return RedirectResponse("/admin", status_code=303)

    new_user = User(
        username=username_clean,
        full_name=full_name_clean,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(new_user)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        flash(request, "Could not create the user due to a database error. Please try again.", "error")
        return RedirectResponse("/admin", status_code=303)
    flash(request, f"User '{username_clean}' created successfully.", "success")
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/users/{user_id}/update")
def update_user(
    request: Request,
    user_id: int,
    full_name: str = Form(""),
    role: str = Form(ROLE_USER),
    is_active: str = Form("on"),
    db: Session = Depends(get_db),
):
    current_user, redirect = _require_admin(request, db)
    if redirect:
        return redirect

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        flash(request, "User not found.", "error")
        return RedirectResponse("/admin", status_code=303)

    if target.role == ROLE_SUPER_ADMIN and not current_user.is_super_admin:
        flash(request, "Only a Super Admin can modify another Super Admin.", "error")
        return RedirectResponse("/admin", status_code=303)

    if role == ROLE_SUPER_ADMIN and not current_user.is_super_admin:
        flash(request, "Only a Super Admin can promote a user to Super Admin.", "error")
        return RedirectResponse("/admin", status_code=303)

    if role not in ALL_ROLES:
        role = target.role

    active_admin_level = _active_admin_level_count(db)
    demoting_last_admin = (
        target.role in ADMIN_LEVEL_ROLES
        and (role not in ADMIN_LEVEL_ROLES or is_active != "on")
        and active_admin_level <= 1
    )
    if demoting_last_admin:
        flash(request, "You cannot remove the last active administrator.", "error")
        return RedirectResponse("/admin", status_code=303)

    full_name_clean = full_name.strip()
    if len(full_name_clean) > FULL_NAME_MAX_LEN:
        flash(request, f"Full name is too long (max {FULL_NAME_MAX_LEN} characters).", "error")
        return RedirectResponse("/admin", status_code=303)

    target.full_name = full_name_clean
    target.role = role
    target.is_active = is_active == "on"
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        flash(request, "Could not update the user due to a database error. Please try again.", "error")
        return RedirectResponse("/admin", status_code=303)
    flash(request, f"User '{target.username}' updated successfully.", "success")
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/users/{user_id}/reset-password")
def reset_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user, redirect = _require_admin(request, db)
    if redirect:
        return redirect

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        flash(request, "User not found.", "error")
        return RedirectResponse("/admin", status_code=303)

    if target.role == ROLE_SUPER_ADMIN and not current_user.is_super_admin:
        flash(request, "Only a Super Admin can reset another Super Admin's password.", "error")
        return RedirectResponse("/admin", status_code=303)

    if not new_password or len(new_password) < 6:
        flash(request, "Password must be at least 6 characters.", "error")
        return RedirectResponse("/admin", status_code=303)

    target.password_hash = hash_password(new_password)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        flash(request, "Could not reset the password due to a database error. Please try again.", "error")
        return RedirectResponse("/admin", status_code=303)
    flash(request, f"Password reset for '{target.username}'.", "success")
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/users/{user_id}/delete")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    current_user, redirect = _require_admin(request, db)
    if redirect:
        return redirect

    if current_user.id == user_id:
        flash(request, "You cannot delete your own account while logged in.", "error")
        return RedirectResponse("/admin", status_code=303)

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        flash(request, "User not found.", "error")
        return RedirectResponse("/admin", status_code=303)

    if target.role == ROLE_SUPER_ADMIN and not current_user.is_super_admin:
        flash(request, "Only a Super Admin can delete another Super Admin.", "error")
        return RedirectResponse("/admin", status_code=303)

    if target.role in ADMIN_LEVEL_ROLES:
        if _active_admin_level_count(db) <= 1:
            flash(request, "You cannot delete the last administrator.", "error")
            return RedirectResponse("/admin", status_code=303)

    username = target.username
    db.delete(target)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        flash(request, "Could not delete the user due to a database error. Please try again.", "error")
        return RedirectResponse("/admin", status_code=303)
    flash(request, f"User '{username}' deleted.", "success")
    return RedirectResponse("/admin", status_code=303)
