# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from typing import TypeVar

from pydantic import Field

from .common import (
    AcademicSessionMinResponse,
    ActiveSchema,
    BaseSchema,
    ClassRoomMinResponse,
    SubjectMinResponse,
    TeacherProfileMinResponse,
    TimestampSchema,
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# ClassRoomBase
# ============================================================


class ClassRoomBase(BaseSchema):
    class_code: str = Field(..., min_length=1, max_length=30)
    class_name: str = Field(..., min_length=1, max_length=100)
    section: str = Field(..., min_length=1, max_length=30)
    display_name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None


# ============================================================
# ClassRoomCreate
# ============================================================


class ClassRoomCreate(ClassRoomBase):
    academic_sessions_id: str
    class_teacher_id: str | None = None


# ============================================================
# ClassRoomUpdate
# ============================================================


class ClassRoomUpdate(BaseSchema):
    class_name: str | None = None
    section: str | None = None
    display_name: str | None = None
    description: str | None = None
    class_teacher_id: str | None = None
    is_active: bool | None = None


# ============================================================
# ClassRoomResponse
# ============================================================


class ClassRoomResponse(ClassRoomBase, TimestampSchema, ActiveSchema):
    academic_sessions_id: str
    class_teacher_id: str | None = None
    created_by: str | None = None
    updated_by: str | None = None

    academic_sessions: AcademicSessionMinResponse | None = None
    class_teacher: TeacherProfileMinResponse | None = None


# ============================================================
# SubjectBase
# ============================================================


class SubjectBase(BaseSchema):
    subject_code: str = Field(..., min_length=1, max_length=30)
    subject_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    display_order: int = Field(0, ge=0)
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
    subject_name: str | None = None
    description: str | None = None
    display_order: int | None = None
    subject_type: str | None = None
    is_active: bool | None = None


# ============================================================
# SubjectResponse
# ============================================================


class SubjectResponse(SubjectBase, TimestampSchema, ActiveSchema):
    created_by: str | None = None
    updated_by: str | None = None


# ============================================================
# ClassSubjectBase
# ============================================================


class ClassSubjectBase(BaseSchema):
    display_order: int = Field(1, ge=1)


# ============================================================
# ClassSubjectCreate
# ============================================================


class ClassSubjectCreate(ClassSubjectBase):
    academic_sessions_id: str
    classroom_id: str
    subject_id: str


# ============================================================
# ClassSubjectResponse
# ============================================================


class ClassSubjectResponse(ClassSubjectBase, TimestampSchema, ActiveSchema):
    class_subject_code: str
    academic_sessions_id: str
    classroom_id: str
    subject_id: str
    created_by: str | None = None
    updated_by: str | None = None

    classroom: ClassRoomMinResponse | None = None
    subject: SubjectMinResponse | None = None
