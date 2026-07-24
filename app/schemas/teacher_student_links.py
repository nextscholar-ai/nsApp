# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import date
from typing import TypeVar

from pydantic import Field

from .common import (
    ActiveSchema,
    BaseSchema,
    ClassRoomMinResponse,
    StudentProfileMinResponse,
    SubjectMinResponse,
    TeacherProfileMinResponse,
    TimestampSchema,
    UserMinResponse,
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# TeacherSubjectBase
# ============================================================


class TeacherSubjectBase(BaseSchema):
    is_class_teacher: bool = False
    remarks: str | None = Field(None, max_length=300)


# ============================================================
# TeacherSubjectCreate
# ============================================================


class TeacherSubjectCreate(TeacherSubjectBase):
    academic_sessions_id: str
    class_subject_id: str
    classroom_id: str
    subject_id: str
    teacher_id: str


# ============================================================
# TeacherSubjectResponse
# ============================================================


class TeacherSubjectResponse(TeacherSubjectBase, TimestampSchema, ActiveSchema):
    teacher_subject_code: str
    academic_sessions_id: str
    class_subject_id: str
    classroom_id: str
    subject_id: str
    teacher_id: str

    classroom: ClassRoomMinResponse | None = None
    subject: SubjectMinResponse | None = None
    teacher: TeacherProfileMinResponse | None = None


# ============================================================
# StudentClassBase
# ============================================================


class StudentClassBase(BaseSchema):
    roll_number: int = Field(..., ge=1)
    admission_date: date
    status: str = "ACTIVE"
    roll_number_locked: bool = False
    remarks: str | None = Field(None, max_length=500)


# ============================================================
# StudentClassCreate
# ============================================================


class StudentClassCreate(StudentClassBase):
    academic_sessions_id: str
    student_id: str
    classroom_id: str


# ============================================================
# StudentClassResponse
# ============================================================


class StudentClassResponse(StudentClassBase, TimestampSchema, ActiveSchema):
    student_class_code: str
    academic_sessions_id: str
    student_id: str
    classroom_id: str

    student: StudentProfileMinResponse | None = None
    classroom: ClassRoomMinResponse | None = None


# ============================================================
# StudentPromotionHistoryBase
# ============================================================


class StudentPromotionHistoryBase(BaseSchema):
    previous_roll_number: int
    new_roll_number: int
    promotion_date: date
    promotion_type: str = "PROMOTED"
    remarks: str | None = Field(None, max_length=500)


# ============================================================
# StudentPromotionHistoryCreate
# ============================================================


class StudentPromotionHistoryCreate(StudentPromotionHistoryBase):
    student_id: str
    from_session_id: str
    to_session_id: str
    from_classroom_id: str
    to_classroom_id: str
    promoted_by_user_id: int | None = None


# ============================================================
# StudentPromotionHistoryResponse
# ============================================================


class StudentPromotionHistoryResponse(StudentPromotionHistoryBase, TimestampSchema):
    promotion_code: str
    student_id: str
    from_session_id: str
    to_session_id: str
    from_classroom_id: str
    to_classroom_id: str
    promoted_by_user_id: str | None = None

    student: StudentProfileMinResponse | None = None
    promoted_by: UserMinResponse | None = None
