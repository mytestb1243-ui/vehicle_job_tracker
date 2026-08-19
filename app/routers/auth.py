from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import verify_password, hash_password
from app.choices import SIGNUP_DEFAULT_ROLE, USERNAME_MAX_LEN, FULL_NAME_MAX_LEN, PASSWORD_MIN_LEN
from app.dependencies import get_current_user, flash, get_flashed_messages
from app.render import templates

router = APIRouter()


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "messages": get_flashed_messages(request),
        },
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username_clean = username.strip().lower()
    user = db.query(User).filter(User.username == username_clean).first()

    if not user or not verify_password(password, user.password_hash):
        flash(request, "Invalid username or password.", "error")
        return RedirectResponse("/login", status_code=303)

    if not user.is_approved:
        flash(request, "Your account is pending administrator approval. You'll be able to sign in once it's approved.", "error")
        return RedirectResponse("/login", status_code=303)

    if not user.is_active:
        flash(request, "Your account has been disabled. Contact an administrator.", "error")
        return RedirectResponse("/login", status_code=303)

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    flash(request, f"Welcome back, {user.full_name or user.username}!", "success")
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/signup")
def signup_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(
        request,
        "signup.html",
        {
            "messages": get_flashed_messages(request),
        },
    )


@router.post("/signup")
def signup_submit(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    full_name_clean = full_name.strip()
    username_clean = username.strip().lower()

    if not full_name_clean or not username_clean or not password:
        flash(request, "Full name, username and password are required.", "error")
        return RedirectResponse("/signup", status_code=303)

    if len(username_clean) > USERNAME_MAX_LEN:
        flash(request, f"Username is too long (max {USERNAME_MAX_LEN} characters).", "error")
        return RedirectResponse("/signup", status_code=303)

    if len(full_name_clean) > FULL_NAME_MAX_LEN:
        flash(request, f"Full name is too long (max {FULL_NAME_MAX_LEN} characters).", "error")
        return RedirectResponse("/signup", status_code=303)

    if password != confirm_password:
        flash(request, "Passwords do not match.", "error")
        return RedirectResponse("/signup", status_code=303)

    if len(password) < PASSWORD_MIN_LEN:
        flash(request, f"Password must be at least {PASSWORD_MIN_LEN} characters.", "error")
        return RedirectResponse("/signup", status_code=303)

    existing = db.query(User).filter(User.username == username_clean).first()
    if existing:
        flash(request, f"Username '{username_clean}' is already taken.", "error")
        return RedirectResponse("/signup", status_code=303)

    new_user = User(
        username=username_clean,
        full_name=full_name_clean,
        password_hash=hash_password(password),
        role=SIGNUP_DEFAULT_ROLE,
        is_active=True,
        is_approved=False,
    )
    db.add(new_user)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        flash(request, "Could not create your account due to a database error. Please try again.", "error")
        return RedirectResponse("/signup", status_code=303)

    flash(
        request,
        "Account request submitted! An administrator will review and approve your account before you can sign in.",
        "success",
    )
    return RedirectResponse("/login", status_code=303)
