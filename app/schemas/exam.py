# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import date, datetime, time
from typing import TypeVar

from pydantic import Field

from app.core.enums import ExamStatus

from .common import (
    ActiveSchema,
    BaseSchema,
    ClassRoomMinResponse,
    TimestampSchema,
)
from .teacher_student_links import StudentClassResponse

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# ExamBase
# ============================================================


class ExamBase(BaseSchema):
    exam_id: str = Field(..., max_length=30)
    exam_name: str = Field(..., max_length=150)
    exam_type: str = Field(..., max_length=50)
    description: str | None = None
    exam_date: date
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    room_number: str | None = Field(None, max_length=50)
    total_marks: float
    passing_marks: float
    status: ExamStatus = ExamStatus.DRAFT
    publish_at: datetime | None = None
    completed_at: datetime | None = None
    total_students: int = 0
    result_uploaded: int = 0


# ============================================================
# ExamCreate
# ============================================================


class ExamCreate(ExamBase):
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: int
    teacher_subject_id: int
    created_by: int


# ============================================================
# ExamResponse
# ============================================================


class ExamResponse(ExamBase, TimestampSchema, ActiveSchema):
    exam_code: str
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: str
    teacher_subject_id: str
    created_by: str
    updated_by: str | None = None
    deleted_by: str | None = None

    classroom: ClassRoomMinResponse | None = None


# ============================================================
# ExamResultBase
# ============================================================


class ExamResultBase(BaseSchema):
    obtained_marks: float = 0.0
    percentage: float = 0.0
    grade: str | None = Field(None, max_length=10)
    remarks: str | None = None
    rank_in_class: int | None = None
    is_absent: bool = False
    checked_at: datetime | None = None


# ============================================================
# ExamResultCreate
# ============================================================


class ExamResultCreate(ExamResultBase):
    exam_id: int
    student_class_id: int
    checked_by: int | None = None


# ============================================================
# ExamResultResponse
# ============================================================


class ExamResultResponse(ExamResultBase, TimestampSchema, ActiveSchema):
    exam_result_code: str
    exam_id: str
    student_class_id: str
    checked_by: str | None = None

    student_class: StudentClassResponse | None = None


# ============================================================
# ExamUpdate
# ============================================================


class ExamUpdate(BaseSchema):
    exam_name: str | None = Field(None, max_length=150)
    exam_type: str | None = Field(None, max_length=50)
    description: str | None = None
    exam_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    room_number: str | None = Field(None, max_length=50)
    total_marks: float | None = None
    passing_marks: float | None = None
    status: ExamStatus | None = None
    publish_at: datetime | None = None
    completed_at: datetime | None = None
    is_active: bool | None = None


# ============================================================
# ExamResultUpdate
# ============================================================


class ExamResultUpdate(BaseSchema):
    obtained_marks: float | None = None
    percentage: float | None = None
    grade: str | None = Field(None, max_length=10)
    remarks: str | None = None
    rank_in_class: int | None = None
    is_absent: bool | None = None
    checked_at: datetime | None = None
    checked_by: int | None = None
