"""
Request / response models for the external REST API.

These define the public contract given to external teams — changing a
field name or removing a field here is a breaking change and belongs in a
new API version (/api/v2), not an edit to v1.
"""
import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.choices import (
    COMPANY_NAME_OPTIONS,
    FULL_NAME_MAX_LEN,
    PASSWORD_MIN_LEN,
    USERNAME_MAX_LEN,
    clean_company_list,
)
from app.api.permissions import API_ASSIGNABLE_ROLES

T = TypeVar("T")

LOCATION_MAX_LEN = 200  # must match Job.location VARCHAR(200)


def _validate_companies(value: Optional[List[str]]) -> Optional[List[str]]:
    if value is None:
        return None
    unknown = [c for c in value if c.strip() not in COMPANY_NAME_OPTIONS]
    if unknown:
        raise ValueError(f"Unknown company name(s): {', '.join(unknown)}")
    return clean_company_list(value)


def _validate_role(value: Optional[str]) -> Optional[str]:
    if value is not None and value not in API_ASSIGNABLE_ROLES:
        raise ValueError(f"role must be one of: {', '.join(API_ASSIGNABLE_ROLES)}")
    return value


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int = Field(description="Total matching records across all pages.")
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    is_approved: bool
    companies: List[str] = Field(
        description="Companies this user is restricted to. Empty list = all companies."
    )
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_user(cls, user) -> "UserOut":
        data = {name: getattr(user, name) for name in cls.model_fields if name != "companies"}
        return cls(**data, companies=user.company_list)


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=USERNAME_MAX_LEN, examples=["ali.khan"])
    full_name: str = Field("", max_length=FULL_NAME_MAX_LEN, examples=["Ali Khan"])
    password: str = Field(min_length=PASSWORD_MIN_LEN, max_length=128)
    role: str = Field("user", examples=["user"])
    companies: List[str] = Field(default_factory=list, examples=[["DHL PAK"]])

    @field_validator("username")
    @classmethod
    def _clean_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("username must not be blank")
        return v

    @field_validator("full_name")
    @classmethod
    def _clean_full_name(cls, v: str) -> str:
        return v.strip()

    _check_role = field_validator("role")(_validate_role)
    _check_companies = field_validator("companies")(_validate_companies)


class UserUpdate(BaseModel):
    """Every field is optional — only the fields sent are changed."""

    full_name: Optional[str] = Field(None, max_length=FULL_NAME_MAX_LEN)
    password: Optional[str] = Field(None, min_length=PASSWORD_MIN_LEN, max_length=128)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    companies: Optional[List[str]] = Field(
        None, description="Replaces the full list. Send [] to give access to all companies."
    )

    @field_validator("full_name")
    @classmethod
    def _clean_full_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v is not None else None

    _check_role = field_validator("role")(_validate_role)
    _check_companies = field_validator("companies")(_validate_companies)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
class JobCreator(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str


class JobOut(BaseModel):
    id: int
    location: str
    date: datetime.date
    created_by: Optional[JobCreator] = Field(
        description="User who created the job. null if that user was deleted."
    )

    @classmethod
    def from_job(cls, job) -> "JobOut":
        creator = JobCreator.model_validate(job.creator) if job.creator else None
        return cls(id=job.id, location=job.location, date=job.job_date, created_by=creator)


class JobLocationUpdate(BaseModel):
    location: str = Field(min_length=1, max_length=LOCATION_MAX_LEN, examples=["Lahore"])

    @field_validator("location")
    @classmethod
    def _clean_location(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("location must not be blank")
        return v
