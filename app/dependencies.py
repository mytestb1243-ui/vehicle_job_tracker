from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import User


def get_current_user(request: Request, db: Session) -> Optional[User]:
    """Return the logged in User object, or None if not authenticated."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None
    return user


def flash(request: Request, message: str, category: str = "info") -> None:
    """Queue a one-time flash message stored in the signed session cookie."""
    bucket = request.session.setdefault("flash_messages", [])
    bucket.append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    """Pop and return all queued flash messages."""
    return request.session.pop("flash_messages", [])
