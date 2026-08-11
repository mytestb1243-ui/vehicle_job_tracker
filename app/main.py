from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.routers import auth, dashboard, search, admin

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="vjt_session",
    max_age=settings.SESSION_MAX_AGE,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router, tags=["auth"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(search.router, tags=["search"])
app.include_router(admin.router, tags=["admin"])


@app.get("/")
def root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/login", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok"}
