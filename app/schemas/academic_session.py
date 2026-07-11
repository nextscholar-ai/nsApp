# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional, Generic, TypeVar, List, Dict, Any, Union
from datetime import datetime, date, time
from decimal import Decimal
from  enum import Enum

from app.core.enums import (
    UserRole, 
    AssignmentStatus, 
    ExamStatus, 
    FeeStatus,
    NoticeType,
    NoticeAudience,
    MaterialType,
    AttendanceStatus,
    LectureStatus,
    PromotionType,
    Gender
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar('T')


from .common import *


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
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_session_dates(self) -> 'AcademicSessionBase':
        if self.end_year <= self.start_year:
            raise ValueError('end_year must be greater than start_year')
        if self.end_date <= self.start_date:
            raise ValueError('end_date must be after start_date')
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
    id: int



# ============================================================
# AcademicSessionUpdate
# ============================================================

class AcademicSessionUpdate(BaseSchema):
    session_code: Optional[str] = Field(None, min_length=3, max_length=20)
    session_name: Optional[str] = Field(None, min_length=1, max_length=20)
    start_year: Optional[int] = Field(None, ge=2000, le=2100)
    end_year: Optional[int] = Field(None, ge=2000, le=2100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
