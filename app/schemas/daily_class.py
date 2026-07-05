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
# DailyClassBase
# ============================================================

class DailyClassBase(BaseSchema):
    daily_class_id: str = Field(..., max_length=30)
    class_date: date
    topic: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    homework: Optional[str] = None
    lecture_status: str = "Scheduled"
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    total_minutes: Optional[int] = None
    remarks: Optional[str] = None


# ============================================================
# DailyClassCreate
# ============================================================

class DailyClassCreate(DailyClassBase):
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    timetable_id: Optional[int] = None


# ============================================================
# DailyClassResponse
# ============================================================

class DailyClassResponse(DailyClassBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    timetable_id: Optional[int] = None
    
    classroom: Optional[ClassRoomMinResponse] = None
    students: List['DailyClassStudentResponse'] = []


# ============================================================
# DailyClassStudentBase
# ============================================================

class DailyClassStudentBase(BaseSchema):
    attendance_status: str = "Present"
    is_late: bool = False
    late_minutes: int = 0
    remarks: Optional[str] = None


# ============================================================
# DailyClassStudentCreate
# ============================================================

class DailyClassStudentCreate(DailyClassStudentBase):
    daily_class_id: int
    student_class_id: int
    marked_by: Optional[int] = None


# ============================================================
# DailyClassStudentResponse
# ============================================================

class DailyClassStudentResponse(DailyClassStudentBase, TimestampSchema):
    id: int
    daily_class_id: int
    student_class_id: int
    marked_by: Optional[int] = None
    marked_at: Optional[datetime] = None
    
    student_class: Optional[StudentClassResponse] = None
    marker: Optional[UserMinResponse] = None


# ============================================================
# StudentAttendanceBase
# ============================================================

class StudentAttendanceBase(BaseSchema):
    total_classes: int = 0
    present_classes: int = 0
    absent_classes: int = 0
    attendance_percentage: float = 0.0


# ============================================================
# StudentAttendanceResponse
# ============================================================

class StudentAttendanceResponse(StudentAttendanceBase, TimestampSchema):
    id: Optional[int] = None
    student_class_id: int



# ============================================================
# DailyClassUpdate
# ============================================================

class DailyClassUpdate(BaseSchema):
    class_date: Optional[date] = None
    topic: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    homework: Optional[str] = None
    lecture_status: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    total_minutes: Optional[int] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================
# DailyClassStudentUpdate
# ============================================================

class DailyClassStudentUpdate(BaseSchema):
    attendance_status: Optional[str] = None
    is_late: Optional[bool] = None
    late_minutes: Optional[int] = None
    remarks: Optional[str] = None
