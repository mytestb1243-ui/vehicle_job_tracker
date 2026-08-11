from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import verify_password
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
