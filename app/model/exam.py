import uuid
import secrets

from sqlalchemy import Enum as SAEnum

from datetime import datetime
from app.core.constants import *
from app.core.enums import *
from app.core.mixins import *
from app.helpers.code_generators import *
from app.helpers.validators import Validators
from app.helpers.date_utils import DateUtils
from app.helpers.security import SecurityUtils


from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    Time,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    Numeric

)

from sqlalchemy.orm import (
    relationship,
    declared_attr
)

from app.api.database import Base


# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# EXAM TABLE
# ============================================================

class Exam(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "exams"

    id = Column(
        Integer,
        primary_key=True
    )

    exam_id = Column(

        String(30),

        unique=True,

        nullable=False,

        default=generate_exam_code,

        index=True

    )

    # =====================================================
    # Academic
    # =====================================================

    academic_sessions_id = Column(

        Integer,

        ForeignKey("academic_sessions.id"),

        nullable=False,

        index=True

    )

    classroom_id = Column(

        Integer,

        ForeignKey("classroom.id"),

        nullable=False,

        index=True

    )

    class_subject_id = Column(

        Integer,

        ForeignKey("class_subjects.id"),

        nullable=False,

        index=True

    )

    teacher_subject_id = Column(

        Integer,

        ForeignKey("teacher_subjects.id"),

        nullable=False,

        index=True

    )

    # =====================================================
    # Exam Details
    # =====================================================

    exam_name = Column(

        String(150),

        nullable=False

    )

    exam_type = Column(

        String(50),

        nullable=False

    )

    description = Column(

        Text

    )

    exam_date = Column(

        Date,

        nullable=False,

        index=True

    )

    start_time = Column(

        Time

    )

    end_time = Column(

        Time

    )

    duration_minutes = Column(

        Integer

    )

    room_number = Column(

        String(50)

    )

    # =====================================================
    # Marks
    # =====================================================

    total_marks = Column(

        Float,

        nullable=False

    )

    passing_marks = Column(

        Float,

        nullable=False

    )

    # =====================================================
    # Status
    # =====================================================

    status = Column(

        SAEnum(ExamStatus),

        default=ExamStatus.DRAFT,

        nullable=False,

        index=True

    )

    publish_at = Column(

        DateTime

    )

    completed_at = Column(

        DateTime

    )

    # =====================================================
    # Statistics
    # =====================================================

    total_students = Column(

        Integer,

        default=0

    )

    result_uploaded = Column(

        Integer,

        default=0

    )

    # =====================================================
    # Audit
    # =====================================================

    created_by = Column(

        Integer,

        ForeignKey("users.id"),

        nullable=False

    )

    updated_by = Column(

        Integer,

        ForeignKey("users.id")

    )

    deleted_by = Column(

        Integer,

        ForeignKey("users.id")

    )

    # =====================================================
    # Relationships
    # =====================================================

    academic_sessions = relationship(
        "AcademicSession"
    )

    classroom = relationship(
        "ClassRoom"
    )

    class_subject = relationship(
        "ClassSubject"
    )

    teacher_subject = relationship(
        "TeacherSubject"
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )

    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )

    deleter = relationship(
        "User",
        foreign_keys=[deleted_by]
    )

    results = relationship(

        "ExamResult",

        back_populates="exam",

        cascade="all, delete-orphan"

    )

    # =====================================================
    # Constraints
    # =====================================================

    __table_args__ = (

        UniqueConstraint(

            "class_subject_id",

            "exam_name",

            "exam_date",

            name="uq_exam"

        ),

        Index(

            "idx_exam_class",

            "classroom_id",

            "exam_date"

        ),

        Index(

            "idx_exam_teacher",

            "teacher_subject_id",

            "status"

        ),

    )


# ============================================================
# EXAMRESULT TABLE
# ============================================================

class ExamResult(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "exam_results"

    id = Column(
        Integer,
        primary_key=True
    )

    exam_id = Column(

        Integer,

        ForeignKey(
            "exams.id"
        ),

        nullable=False,

        index=True

    )

    student_class_id = Column(

        Integer,

        ForeignKey(
            "student_classes.id"
        ),

        nullable=False,

        index=True

    )

    obtained_marks = Column(

        Float,

        nullable=False,

        default=0

    )

    percentage = Column(

        Float,

        default=0

    )

    grade = Column(

        String(10)

    )

    remarks = Column(

        Text

    )

    rank_in_class = Column(

        Integer

    )

    is_absent = Column(

        Boolean,

        default=False

    )

    checked_by = Column(

        Integer,

        ForeignKey(
            "users.id"
        )

    )

    checked_at = Column(

        DateTime

    )

    exam = relationship(

        "Exam",

        back_populates="results"

    )

    student_class = relationship(

        "StudentClass"

    )

    checker = relationship(

        "User"

    )

    __table_args__ = (

        UniqueConstraint(

            "exam_id",

            "student_class_id",

            name="uq_exam_result"

        ),

        Index(

            "idx_exam_result",

            "student_class_id",

            "exam_id"

        ),

        Index(

            "idx_exam_rank",

            "exam_id",

            "rank_in_class"

        ),

    )


