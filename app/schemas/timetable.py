# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import time
from typing import TypeVar

from pydantic import Field, model_validator

from .common import (
    ActiveSchema,
    AuditSchema,
    BaseSchema,
    ClassRoomMinResponse,
    TimestampSchema,
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

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
    pass


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
    def validate_times(self) -> "TimeSlotBase":
        if self.end_time <= self.start_time:
            msg = "end_time must be after start_time"
            raise ValueError(msg)
        return self


# ============================================================
# TimeSlotResponse
# ============================================================


class TimeSlotResponse(TimeSlotBase, TimestampSchema, ActiveSchema):
    pass


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
    room_number: str | None = Field(None, max_length=50)
    remarks: str | None = None


# ============================================================
# ClassTimeTableCreate
# ============================================================


class ClassTimeTableCreate(ClassTimeTableBase):
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: int
    teacher_subject_id: int
    week_day_id: str
    time_slot_id: str


# ============================================================
# ClassTimeTableResponse
# ============================================================


class ClassTimeTableResponse(
    ClassTimeTableBase,
    TimestampSchema,
    ActiveSchema,
    AuditSchema,
):
    timetable_code: str
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: str
    teacher_subject_id: str
    week_day_id: str
    time_slot_id: str

    classroom: ClassRoomMinResponse | None = None
    week_day: WeekDayResponse | None = None
    time_slot: TimeSlotResponse | None = None


# ============================================================
# ClassTimeTableUpdate
# ============================================================


class ClassTimeTableUpdate(BaseSchema):
    room_number: str | None = Field(None, max_length=50)
    remarks: str | None = None
    academic_sessions_id: str | None = None
    classroom_id: str | None = None
    class_subject_id: int | None = None
    teacher_subject_id: int | None = None
    week_day_id: str | None = None
    time_slot_id: str | None = None
    is_active: bool | None = None


# ============================================================
# TeacherAvailabilityBase
# ============================================================


class TeacherAvailabilityBase(BaseSchema):
    availability_id: str = Field(..., max_length=30)
    is_available: bool = True
    reason: str | None = Field(None, max_length=255)
    remarks: str | None = None


# ============================================================
# TeacherAvailabilityCreate
# ============================================================


class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    academic_sessions_id: str
    teacher_subject_id: int
    week_day_id: str
    time_slot_id: str


# ============================================================
# TeacherAvailabilityResponse
# ============================================================


class TeacherAvailabilityResponse(
    TeacherAvailabilityBase,
    TimestampSchema,
    ActiveSchema,
    AuditSchema,
):
    id: int
    academic_sessions_id: str
    teacher_subject_id: int
    week_day_id: str
    time_slot_id: str

    week_day: WeekDayResponse | None = None
    time_slot: TimeSlotResponse | None = None


# ============================================================
# TeacherAvailabilityUpdate
# ============================================================


class TeacherAvailabilityUpdate(BaseSchema):
    is_available: bool | None = None
    reason: str | None = Field(None, max_length=255)
    remarks: str | None = None
    academic_sessions_id: str | None = None
    teacher_subject_id: int | None = None
    week_day_id: str | None = None
    time_slot_id: str | None = None
