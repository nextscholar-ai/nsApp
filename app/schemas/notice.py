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
# NoticeBase
# ============================================================

class NoticeBase(BaseSchema):
    notice_id: str = Field(..., max_length=30)
    title: str = Field(..., max_length=250)
    description: str
    notice_type: NoticeType = NoticeType.GENERAL
    audience: NoticeAudience = NoticeAudience.ALL
    publish_date: date
    expiry_date: Optional[date] = None
    attachment_name: Optional[str] = Field(None, max_length=255)
    attachment_path: Optional[str] = Field(None, max_length=500)
    attachment_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    is_pinned: bool = False


# ============================================================
# NoticeCreate
# ============================================================

class NoticeCreate(NoticeBase):
    academic_sessions_id: int
    classroom_id: Optional[int] = None
    created_by: int


# ============================================================
# NoticeResponse
# ============================================================

class NoticeResponse(NoticeBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    classroom_id: Optional[int] = None
    created_by: int
    updated_by: Optional[int] = None
    deleted_by: Optional[int] = None
    
    classroom: Optional[ClassRoomMinResponse] = None



# ============================================================
# NoticeUpdate
# ============================================================

class NoticeUpdate(BaseSchema):
    title: Optional[str] = Field(None, max_length=250)
    description: Optional[str] = None
    notice_type: Optional[NoticeType] = None
    audience: Optional[NoticeAudience] = None
    publish_date: Optional[date] = None
    expiry_date: Optional[date] = None
    attachment_name: Optional[str] = Field(None, max_length=255)
    attachment_path: Optional[str] = Field(None, max_length=500)
    attachment_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    is_pinned: Optional[bool] = None
    classroom_id: Optional[int] = None
    is_active: Optional[bool] = None


# ============================================================
# NoticeFilterRequest
# ============================================================

class NoticeFilterRequest(BaseSchema):
    notice_type: Optional[NoticeType] = None
    audience: Optional[NoticeAudience] = None
    classroom_id: Optional[int] = None
    is_pinned: Optional[bool] = None
    academic_sessions_id: Optional[int] = None
