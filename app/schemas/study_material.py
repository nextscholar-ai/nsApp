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
# StudyMaterialBase
# ============================================================

class StudyMaterialBase(BaseSchema):
    material_id: str = Field(..., max_length=30)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    material_type: MaterialType
    file_name: str = Field(..., max_length=255)
    file_url: str = Field(..., max_length=500)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    download_count: int = 0


# ============================================================
# StudyMaterialCreate
# ============================================================

class StudyMaterialCreate(StudyMaterialBase):
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    uploaded_by: int


# ============================================================
# StudyMaterialResponse
# ============================================================

class StudyMaterialResponse(StudyMaterialBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    uploaded_by: int
    
    classroom: Optional[ClassRoomMinResponse] = None
    uploader: Optional[UserMinResponse] = None


class StudyMaterialUpdate(BaseSchema):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    material_type: Optional[MaterialType] = None

    academic_sessions_id: Optional[int] = None
    classroom_id: Optional[int] = None
    class_subject_id: Optional[int] = None
    teacher_subject_id: Optional[int] = None



