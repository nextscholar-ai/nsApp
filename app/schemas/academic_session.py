# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import date
from typing import TypeVar

from pydantic import Field, model_validator

from .common import (
    ActiveSchema,
    BaseSchema,
    TimestampSchema,
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# AcademicSessionBase
# ============================================================


class AcademicSessionBase(BaseSchema):
    session_code: str = Field(..., min_length=3, max_length=20)
    session_name: str = Field(..., min_length=1, max_length=20)
    start_year: int = Field(..., ge=2000, le=2200)
    end_year: int = Field(..., ge=2000, le=2200)
    start_date: date
    end_date: date
    is_current: bool = False
    description: str | None = None

    @model_validator(mode="after")
    def validate_session_dates(self) -> "AcademicSessionBase":
        if self.end_year <= self.start_year:
            msg = "end_year must be greater than start_year"
            raise ValueError(msg)
        if self.end_date <= self.start_date:
            msg = "end_date must be after start_date"
            raise ValueError(msg)
        return self


# ============================================================
# AcademicSessionCreate
# ============================================================


class AcademicSessionCreate(AcademicSessionBase):
    pass


# ============================================================
# AcademicSessionResponse
# ============================================================


class AcademicSessionResponse(AcademicSessionBase, TimestampSchema, ActiveSchema):
    pass


# ============================================================
# AcademicSessionUpdate
# ============================================================


class AcademicSessionUpdate(BaseSchema):
    session_code: str | None = Field(None, min_length=3, max_length=20)
    session_name: str | None = Field(None, min_length=1, max_length=20)
    start_year: int | None = Field(None, ge=2000, le=2100)
    end_year: int | None = Field(None, ge=2000, le=2100)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description: str | None = None
    is_active: bool | None = None
