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
# ClassRoomBase
# ============================================================

class ClassRoomBase(BaseSchema):
    class_code: str = Field(..., min_length=1, max_length=30)
    class_name: str = Field(..., min_length=1, max_length=100)
    section: str = Field(..., min_length=1, max_length=30)
    display_name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None


# ============================================================
# ClassRoomCreate
# ============================================================

class ClassRoomCreate(ClassRoomBase):
    academic_sessions_id: int
    class_teacher_id: Optional[str] = None


# ============================================================
# ClassRoomUpdate
# ============================================================

class ClassRoomUpdate(BaseSchema):
    class_name: Optional[str] = None
    section: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    class_teacher_id: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================
# ClassRoomResponse
# ============================================================

class ClassRoomResponse(ClassRoomBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    class_teacher_id: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    academic_sessions: Optional[AcademicSessionMinResponse] = None
    class_teacher: Optional[TeacherProfileMinResponse] = None


# ============================================================
# SubjectBase
# ============================================================

class SubjectBase(BaseSchema):
    subject_code: str = Field(..., min_length=1, max_length=30)
    subject_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    display_order: int = Field(1, ge=1)
    subject_type: str = "Core"


# ============================================================
# SubjectCreate
# ============================================================

class SubjectCreate(SubjectBase):
    pass


# ============================================================
# SubjectUpdate
# ============================================================

class SubjectUpdate(BaseSchema):
    subject_name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    subject_type: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================
# SubjectResponse
# ============================================================

class SubjectResponse(SubjectBase, TimestampSchema, ActiveSchema):
    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


# ============================================================
# ClassSubjectBase
# ============================================================

class ClassSubjectBase(BaseSchema):
    display_order: int = Field(1, ge=1)


# ============================================================
# ClassSubjectCreate
# ============================================================

class ClassSubjectCreate(ClassSubjectBase):
    academic_sessions_id: int
    classroom_id: int
    subject_id: int


# ============================================================
# ClassSubjectResponse
# ============================================================

class ClassSubjectResponse(ClassSubjectBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    classroom_id: int
    subject_id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    classroom: Optional[ClassRoomMinResponse] = None
    subject: Optional[SubjectMinResponse] = None


