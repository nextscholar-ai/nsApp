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
# AssignmentBase
# ============================================================

class AssignmentBase(BaseSchema):
    assignment_id: str = Field(..., max_length=30)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: date
    due_time: Optional[time] = None
    total_marks: float = 0.0
    passing_marks: float = 0.0
    file_name: Optional[str] = Field(None, max_length=255)
    file_path: Optional[str] = Field(None, max_length=500)
    file_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = None
    uploaded_by: Optional[int] = None
    status: AssignmentStatus = AssignmentStatus.DRAFT


    publish_at: Optional[datetime] = None
    close_at: Optional[datetime] = None
    total_students: int = 0
    checked_students: int = 0


# ============================================================
# AssignmentCreate
# ============================================================

class AssignmentCreate(AssignmentBase):
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    created_by: int


# ============================================================
# AssignmentResponse
# ============================================================

class AssignmentResponse(AssignmentBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    created_by: int
    updated_by: Optional[int] = None
    deleted_by: Optional[int] = None
    
    classroom: Optional[ClassRoomMinResponse] = None
    creator: Optional[UserMinResponse] = None


# ============================================================
# AssignmentResultBase
# ============================================================

class AssignmentResultBase(BaseSchema):
    obtained_marks: float = 0.0
    percentage: float = 0.0
    grade: Optional[str] = Field(None, max_length=10)
    remarks: Optional[str] = None
    is_checked: bool = False
    checked_at: Optional[datetime] = None


# ============================================================
# AssignmentResultCreate
# ============================================================

class AssignmentResultCreate(AssignmentResultBase):
    assignment_id: int
    student_class_id: int
    checked_by: Optional[int] = None


# ============================================================
# AssignmentResultResponse
# ============================================================

class AssignmentResultResponse(AssignmentResultBase, TimestampSchema, ActiveSchema):
    id: int
    assignment_id: int
    student_class_id: int
    checked_by: Optional[int] = None
    
    student_class: Optional[StudentClassResponse] = None



# ============================================================
# AssignmentUpdate
# ============================================================

class AssignmentUpdate(BaseSchema):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    total_marks: Optional[float] = None
    passing_marks: Optional[float] = None
    file_name: Optional[str] = Field(None, max_length=255)
    file_path: Optional[str] = Field(None, max_length=500)
    file_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = None
    uploaded_by: Optional[int] = None

    status: Optional[AssignmentStatus] = None
    publish_at: Optional[datetime] = None
    close_at: Optional[datetime] = None
    is_active: Optional[bool] = None


# ============================================================
# AssignmentResultUpdate
# ============================================================

class AssignmentResultUpdate(BaseSchema):
    obtained_marks: Optional[float] = None
    percentage: Optional[float] = None
    grade: Optional[str] = Field(None, max_length=10)
    remarks: Optional[str] = None
    is_checked: Optional[bool] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = None
