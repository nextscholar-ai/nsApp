# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import date, datetime
from typing import TypeVar

from pydantic import Field

from .common import (
    ActiveSchema,
    BaseSchema,
    ClassRoomMinResponse,
    TimestampSchema,
    UserMinResponse,
)
from .teacher_student_links import StudentClassResponse

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# DailyClassBase
# ============================================================


class DailyClassBase(BaseSchema):
    daily_class_id: str = Field(..., max_length=30)
    class_date: date
    topic: str | None = Field(None, max_length=300)
    description: str | None = None
    homework: str | None = None
    lecture_status: str = "Scheduled"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    total_minutes: int | None = None
    remarks: str | None = None


# ============================================================
# DailyClassCreate
# ============================================================


class DailyClassCreate(DailyClassBase):
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: int
    teacher_subject_id: int
    timetable_id: int | None = None


# ============================================================
# DailyClassResponse
# ============================================================


class DailyClassResponse(DailyClassBase, TimestampSchema, ActiveSchema):
    daily_class_code: str
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: str
    teacher_subject_id: str
    timetable_id: str | None = None

    classroom: ClassRoomMinResponse | None = None
    students: list["DailyClassStudentResponse"] = Field(default_factory=list)


# ============================================================
# DailyClassStudentBase
# ============================================================


class DailyClassStudentBase(BaseSchema):
    attendance_status: str = "Present"
    is_late: bool = False
    late_minutes: int = 0
    remarks: str | None = None


# ============================================================
# DailyClassStudentCreate
# ============================================================


class DailyClassStudentCreate(DailyClassStudentBase):
    daily_class_id: int
    student_class_id: int
    marked_by: int | None = None


# ============================================================
# DailyClassStudentResponse
# ============================================================


class DailyClassStudentResponse(DailyClassStudentBase, TimestampSchema):
    daily_class_student_code: str
    daily_class_id: int
    student_class_id: str
    marked_by: str | None = None
    marked_at: datetime | None = None

    student_class: StudentClassResponse | None = None
    marker: UserMinResponse | None = None


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
    attendance_code: str | None = None
    student_class_id: str


# ============================================================
# DailyClassUpdate
# ============================================================


class DailyClassUpdate(BaseSchema):
    class_date: date | None = None
    topic: str | None = Field(None, max_length=300)
    description: str | None = None
    homework: str | None = None
    lecture_status: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    total_minutes: int | None = None
    remarks: str | None = None
    is_active: bool | None = None


# ============================================================
# DailyClassStudentUpdate
# ============================================================


class DailyClassStudentUpdate(BaseSchema):
    attendance_status: str | None = None
    is_late: bool | None = None
    late_minutes: int | None = None
    remarks: str | None = None
