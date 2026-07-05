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
# TeacherSubjectBase
# ============================================================

class TeacherSubjectBase(BaseSchema):
    is_class_teacher: bool = False
    remarks: Optional[str] = Field(None, max_length=300)


# ============================================================
# TeacherSubjectCreate
# ============================================================

class TeacherSubjectCreate(TeacherSubjectBase):
    academic_sessions_id: int
    class_subject_id: int
    classroom_id: int
    subject_id: int
    teacher_id: str


# ============================================================
# TeacherSubjectResponse
# ============================================================

class TeacherSubjectResponse(TeacherSubjectBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    class_subject_id: int
    classroom_id: int
    subject_id: int
    teacher_id: str
    
    classroom: Optional[ClassRoomMinResponse] = None
    subject: Optional[SubjectMinResponse] = None
    teacher: Optional[TeacherProfileMinResponse] = None


# ============================================================
# StudentClassBase
# ============================================================

class StudentClassBase(BaseSchema):
    roll_number: int = Field(..., ge=1)
    admission_date: date
    status: str = "ACTIVE"
    roll_number_locked: bool = False
    remarks: Optional[str] = Field(None, max_length=500)


# ============================================================
# StudentClassCreate
# ============================================================

class StudentClassCreate(StudentClassBase):
    academic_sessions_id: int
    student_id: str
    classroom_id: int


# ============================================================
# StudentClassResponse
# ============================================================

class StudentClassResponse(StudentClassBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    student_id: str
    classroom_id: int
    
    student: Optional[StudentProfileMinResponse] = None
    classroom: Optional[ClassRoomMinResponse] = None


# ============================================================
# StudentPromotionHistoryBase
# ============================================================

class StudentPromotionHistoryBase(BaseSchema):
    previous_roll_number: int
    new_roll_number: int
    promotion_date: date
    promotion_type: str = "PROMOTED"
    remarks: Optional[str] = Field(None, max_length=500)


# ============================================================
# StudentPromotionHistoryCreate
# ============================================================

class StudentPromotionHistoryCreate(StudentPromotionHistoryBase):
    student_id: str
    from_session_id: int
    to_session_id: int
    from_classroom_id: int
    to_classroom_id: int
    promoted_by_user_id: Optional[int] = None


# ============================================================
# StudentPromotionHistoryResponse
# ============================================================

class StudentPromotionHistoryResponse(StudentPromotionHistoryBase, TimestampSchema):
    id: int
    student_id: str
    from_session_id: int
    to_session_id: int
    from_classroom_id: int
    to_classroom_id: int
    promoted_by_user_id: Optional[int] = None
    
    student: Optional[StudentProfileMinResponse] = None
    promoted_by: Optional[UserMinResponse] = None


