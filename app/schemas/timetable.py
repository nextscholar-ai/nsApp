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
# WeekDayBase
# ============================================================

class WeekDayBase(BaseSchema):
    day_code: str = Field(..., min_length=3, max_length=3)
    day_name: str = Field(..., min_length=1, max_length=20)
    display_order: int = Field(1, ge=1, le=7)


# ============================================================
# WeekDayResponse
# ============================================================

class WeekDayResponse(WeekDayBase, TimestampSchema, ActiveSchema):
    id: int


# ============================================================
# WeekDayCreate
# ============================================================

class WeekDayCreate(WeekDayBase):
    pass


# ============================================================
# TimeSlotBase
# ============================================================

class TimeSlotBase(BaseSchema):
    slot_code: str = Field(..., min_length=1, max_length=10)
    slot_name: str = Field(..., min_length=1, max_length=50)
    start_time: time
    end_time: time
    duration_minutes: int = Field(..., gt=0)
    display_order: int = Field(..., ge=1)
    is_break: bool = False

    @model_validator(mode="after")
    def validate_times(self) -> 'TimeSlotBase':
        if self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self


# ============================================================
# TimeSlotResponse
# ============================================================

class TimeSlotResponse(TimeSlotBase, TimestampSchema, ActiveSchema):
    id: int


# ============================================================
# TimeSlotCreate
# ============================================================

class TimeSlotCreate(TimeSlotBase):
    pass


# ============================================================
# ClassTimeTableBase
# ============================================================

class ClassTimeTableBase(BaseSchema):
    timetable_id: str = Field(..., max_length=30)
    room_number: Optional[str] = Field(None, max_length=50)
    remarks: Optional[str] = None


# ============================================================
# ClassTimeTableCreate
# ============================================================

class ClassTimeTableCreate(ClassTimeTableBase):
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    week_day_id: int
    time_slot_id: int


# ============================================================
# ClassTimeTableResponse
# ============================================================

class ClassTimeTableResponse(ClassTimeTableBase, TimestampSchema, ActiveSchema, AuditSchema):
    id: int
    academic_sessions_id: int
    classroom_id: int
    class_subject_id: int
    teacher_subject_id: int
    week_day_id: int
    time_slot_id: int
    
    classroom: Optional[ClassRoomMinResponse] = None
    week_day: Optional[WeekDayResponse] = None
    time_slot: Optional[TimeSlotResponse] = None


# ============================================================
# ClassTimeTableUpdate
# ============================================================

class ClassTimeTableUpdate(BaseSchema):
    room_number: Optional[str] = Field(None, max_length=50)
    remarks: Optional[str] = None
    academic_sessions_id: Optional[int] = None
    classroom_id: Optional[int] = None
    class_subject_id: Optional[int] = None
    teacher_subject_id: Optional[int] = None
    week_day_id: Optional[int] = None
    time_slot_id: Optional[int] = None
    is_active: Optional[bool] = None


# ============================================================
# TeacherAvailabilityBase
# ============================================================

class TeacherAvailabilityBase(BaseSchema):
    availability_id: str = Field(..., max_length=30)
    is_available: bool = True
    reason: Optional[str] = Field(None, max_length=255)
    remarks: Optional[str] = None


# ============================================================
# TeacherAvailabilityCreate
# ============================================================

class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    academic_sessions_id: int
    teacher_subject_id: int
    week_day_id: int
    time_slot_id: int


# ============================================================
# TeacherAvailabilityResponse
# ============================================================

class TeacherAvailabilityResponse(TeacherAvailabilityBase, TimestampSchema, ActiveSchema, AuditSchema):
    id: int
    academic_sessions_id: int
    teacher_subject_id: int
    week_day_id: int
    time_slot_id: int
    
    week_day: Optional[WeekDayResponse] = None
    time_slot: Optional[TimeSlotResponse] = None



# ============================================================
# TeacherAvailabilityUpdate
# ============================================================

class TeacherAvailabilityUpdate(BaseSchema):
    is_available: Optional[bool] = None
    reason: Optional[str] = Field(None, max_length=255)
    remarks: Optional[str] = None
    academic_sessions_id: Optional[int] = None
    teacher_subject_id: Optional[int] = None
    week_day_id: Optional[int] = None
    time_slot_id: Optional[int] = None
