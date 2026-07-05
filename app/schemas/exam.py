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
from .teacher_student_links import StudentClassResponse


# ============================================================
# ExamBase
# ============================================================

class ExamBase(BaseSchema):
    exam_id: str = Field(..., max_length=30)
    exam_name: str = Field(..., max_length=150)
    exam_type: str = Field(..., max_length=50)
    description: Optional[str] = None
    exam_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    room_number: Optional[str] = Field(None, max_length=50)
    total_marks: float
    passing_marks: float
    status: ExamStatus = ExamStatus.DRAFT
    publish_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_students: int = 0
    result_uploaded: int = 0


# ============================================================
# ExamCreate
# ============================================================

class ExamCreate(ExamBase):
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    created_by: int


# ============================================================
# ExamResponse
# ============================================================

class ExamResponse(ExamBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    created_by: int
    updated_by: Optional[int] = None
    deleted_by: Optional[int] = None
    
    classroom: Optional[ClassRoomMinResponse] = None


# ============================================================
# ExamResultBase
# ============================================================

class ExamResultBase(BaseSchema):
    obtained_marks: float = 0.0
    percentage: float = 0.0
    grade: Optional[str] = Field(None, max_length=10)
    remarks: Optional[str] = None
    rank_in_class: Optional[int] = None
    is_absent: bool = False
    checked_at: Optional[datetime] = None


# ============================================================
# ExamResultCreate
# ============================================================

class ExamResultCreate(ExamResultBase):
    exam_id: int
    student_class_id: int
    checked_by: Optional[int] = None


# ============================================================
# ExamResultResponse
# ============================================================

class ExamResultResponse(ExamResultBase, TimestampSchema, ActiveSchema):
    id: int
    exam_id: int
    student_class_id: int
    checked_by: Optional[int] = None
    
    student_class: Optional[StudentClassResponse] = None



# ============================================================
# ExamUpdate
# ============================================================

class ExamUpdate(BaseSchema):
    exam_name: Optional[str] = Field(None, max_length=150)
    exam_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    room_number: Optional[str] = Field(None, max_length=50)
    total_marks: Optional[float] = None
    passing_marks: Optional[float] = None
    status: Optional[ExamStatus] = None
    publish_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_active: Optional[bool] = None


# ============================================================
# ExamResultUpdate
# ============================================================

class ExamResultUpdate(BaseSchema):
    obtained_marks: Optional[float] = None
    percentage: Optional[float] = None
    grade: Optional[str] = Field(None, max_length=10)
    remarks: Optional[str] = None
    rank_in_class: Optional[int] = None
    is_absent: Optional[bool] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = None
