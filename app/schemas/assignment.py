# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import date, datetime, time
from typing import TypeVar

from pydantic import Field

from app.core.enums import AssignmentStatus

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
# AssignmentBase
# ============================================================


class AssignmentBase(BaseSchema):
    assignment_id: str = Field(..., max_length=30)
    title: str = Field(..., max_length=200)
    description: str | None = None
    instructions: str | None = None
    due_date: date
    due_time: time | None = None
    total_marks: float = 0.0
    passing_marks: float = 0.0
    file_name: str | None = Field(None, max_length=255)
    file_path: str | None = Field(None, max_length=500)
    file_type: str | None = Field(None, max_length=100)
    file_size: int | None = None
    uploaded_by: str | None = None
    status: AssignmentStatus = AssignmentStatus.DRAFT

    publish_at: datetime | None = None
    close_at: datetime | None = None
    total_students: int = 0
    checked_students: int = 0


# ============================================================
# AssignmentCreate
# ============================================================


class AssignmentCreate(AssignmentBase):
    assignment_id: str | None = Field(None, max_length=30)
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: str
    teacher_subject_id: str
    created_by: str | None = None


# ============================================================
# AssignmentResponse
# ============================================================


class AssignmentResponse(AssignmentBase, TimestampSchema, ActiveSchema):
    assignment_id: str | None = Field(None, max_length=30)
    assignment_code: str
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: str
    teacher_subject_id: str
    created_by: str
    updated_by: str | None = None
    deleted_by: str | None = None

    classroom: ClassRoomMinResponse | None = None
    creator: UserMinResponse | None = None


# ============================================================
# AssignmentResultBase
# ============================================================


class AssignmentResultBase(BaseSchema):
    obtained_marks: float = 0.0
    percentage: float = 0.0
    grade: str | None = Field(None, max_length=10)
    remarks: str | None = None
    is_checked: bool = False
    checked_at: datetime | None = None


# ============================================================
# AssignmentResultCreate
# ============================================================


class AssignmentResultCreate(AssignmentResultBase):
    assignment_id: str
    student_class_id: str
    checked_by: str | None = None


# ============================================================
# AssignmentResultResponse
# ============================================================


class AssignmentResultResponse(AssignmentResultBase, TimestampSchema, ActiveSchema):
    assignment_result_code: str
    assignment_id: str
    student_class_id: str
    checked_by: str | None = None

    student_class: StudentClassResponse | None = None


# ============================================================
# AssignmentUpdate
# ============================================================


class AssignmentUpdate(BaseSchema):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    instructions: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    total_marks: float | None = None
    passing_marks: float | None = None
    file_name: str | None = Field(None, max_length=255)
    file_path: str | None = Field(None, max_length=500)
    file_type: str | None = Field(None, max_length=100)
    file_size: int | None = None
    uploaded_by: str | None = None

    status: AssignmentStatus | None = None
    publish_at: datetime | None = None
    close_at: datetime | None = None
    is_active: bool | None = None


# ============================================================
# AssignmentResultUpdate
# ============================================================


class AssignmentResultUpdate(BaseSchema):
    obtained_marks: float | None = None
    percentage: float | None = None
    grade: str | None = Field(None, max_length=10)
    remarks: str | None = None
    is_checked: bool | None = None
    checked_at: datetime | None = None
    checked_by: str | None = None
