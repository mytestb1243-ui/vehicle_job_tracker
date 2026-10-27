"""
API-key authentication for the external REST API.

Clients send their key in the `X-API-Key` header. Keys are issued and
revoked with scripts/manage_api_keys.py; only a SHA-256 hash is stored.
"""
import datetime
import hashlib
import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey

API_KEY_HEADER = "X-API-Key"
KEY_PREFIX = "vjt_"

# How often last_used_at is written, so every request doesn't cost a DB write.
LAST_USED_RESOLUTION = datetime.timedelta(minutes=5)

api_key_header = APIKeyHeader(
    name=API_KEY_HEADER,
    auto_error=False,
    description="API key issued by the Vehicle Job Tracker administrators.",
)


def hash_key(plain_key: str) -> str:
    return hashlib.sha256(plain_key.encode("utf-8")).hexdigest()


def generate_key() -> str:
    """Return a new random plain-text key, e.g. 'vjt_3q2...'."""
    return KEY_PREFIX + secrets.token_urlsafe(32)


def require_api_key(
    plain_key: str | None = Security(api_key_header),
    db: Session = Depends(get_db),
) -> ApiKey:
    """Dependency: reject the request with 401 unless a valid, active key is sent."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid API key.",
        headers={"WWW-Authenticate": API_KEY_HEADER},
    )
    if not plain_key:
        raise unauthorized

    api_key = db.query(ApiKey).filter(ApiKey.key_hash == hash_key(plain_key)).first()
    if not api_key or not api_key.is_active:
        raise unauthorized

    now = datetime.datetime.utcnow()
    if not api_key.last_used_at or now - api_key.last_used_at > LAST_USED_RESOLUTION:
        api_key.last_used_at = now
        db.commit()
    return api_key
