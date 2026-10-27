"""
External REST API, version 1 — mounted at /api/v1 by app/main.py.

It is a separate FastAPI sub-application so it gets its own interactive
docs (/api/v1/docs) that list only the API, not the web pages.
"""
from fastapi import FastAPI

from app.api import jobs, users
from app.config import settings

API_DESCRIPTION = """
REST API for the Vehicle Job Tracker.

**Authentication:** send your API key in the `X-API-Key` header on every
request. Click **Authorize** above to try requests from this page.

Full guide: `docs/API.md` in the project repository.
"""

api_v1 = FastAPI(
    title=f"{settings.APP_NAME} API",
    version="1.0.0",
    description=API_DESCRIPTION,
)

api_v1.include_router(users.router)
api_v1.include_router(jobs.router)
