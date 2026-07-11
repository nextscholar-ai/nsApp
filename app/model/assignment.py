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
# ASSIGNMENT TABLE
# ============================================================

class Assignment(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "assignments"

    id = Column(
        Integer,
        primary_key=True
    )

    assignment_id = Column(
        String(30),
        unique=True,
        nullable=False,
        default=generate_assignment_id,
        index=True
    )

    # =====================================================
    # Academic
    # =====================================================

    academic_sessions_id = Column(

        Integer,

        ForeignKey(
            "academic_sessions.id"
        ),

        nullable=False,

        index=True

    )

    classroom_id = Column(

        Integer,

        ForeignKey(
            "classroom.id"
        ),

        nullable=False,

        index=True

    )

    class_subject_id = Column(

        Integer,

        ForeignKey(
            "class_subjects.id"
        ),

        nullable=False,

        index=True

    )

    teacher_subject_id = Column(

        Integer,

        ForeignKey(
            "teacher_subjects.id"
        ),

        nullable=False,

        index=True

    )

    # =====================================================
    # Assignment
    # =====================================================

    title = Column(

        String(200),

        nullable=False

    )

    description = Column(

        Text,

        nullable=True

    )

    instructions = Column(

        Text,

        nullable=True

    )

    due_date = Column(

        Date,

        nullable=False,

        index=True

    )

    due_time = Column(

        Time,

        nullable=True

    )

    total_marks = Column(

        Float,

        nullable=False,

        default=0

    )

    passing_marks = Column(

        Float,

        nullable=False,

        default=0

    )

    # =====================================================
    # Attachment (Uploaded File)
    # =====================================================

    file_name = Column(

        String(255),

        nullable=True

    )

    file_path = Column(

        String(500),

        nullable=True

    )


    file_type = Column(

        String(100),

        nullable=True

    )

    file_size = Column(

        Integer,

        nullable=True

    )

    uploaded_by = Column(

        Integer,

        ForeignKey("users.id"),

        nullable=True

    )









    # =====================================================
    # Status
    # =====================================================

    status = Column(

        SAEnum(AssignmentStatus),

        nullable=False,

        default=AssignmentStatus.DRAFT,

        index=True

    )

    publish_at = Column(

        DateTime,

        nullable=True

    )

    close_at = Column(

        DateTime,

        nullable=True

    )

    # =====================================================
    # Statistics
    # =====================================================

    total_students = Column(

        Integer,

        default=0

    )

    checked_students = Column(

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

        ForeignKey("users.id"),

        nullable=True

    )

    deleted_by = Column(

        Integer,

        ForeignKey("users.id"),

        nullable=True

    )

    academic_sessionss = relationship(
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

        "AssignmentResult",

        back_populates="assignment",

        cascade="all, delete-orphan"

    )

    __table_args__ = (

        UniqueConstraint(

            "class_subject_id",

            "title",

            "due_date",

            name="uq_assignment"

        ),

        Index(

            "idx_assignment_class",

            "classroom_id",

            "due_date"

        ),

        Index(

            "idx_assignment_teacher",

            "teacher_subject_id",

            "status"

        ),

        Index(

            "idx_assignment_session",

            "academic_sessions_id",

            "status"

        ),

    )


# ============================================================
# ASSIGNMENTRESULT TABLE
# ============================================================

class AssignmentResult(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "assignment_results"

    id = Column(
        Integer,
        primary_key=True
    )

    # ===========================================
    # Relations
    # ===========================================

    assignment_id = Column(

        Integer,

        ForeignKey(
            "assignments.id"
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

    # ===========================================
    # Marks
    # ===========================================

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

    # ===========================================
    # Status
    # ===========================================

    is_checked = Column(

        Boolean,

        default=False,

        nullable=False

    )

    checked_at = Column(

        DateTime

    )

    # ===========================================
    # Audit
    # ===========================================

    checked_by = Column(

        Integer,

        ForeignKey("users.id")

    )

    assignment = relationship(
        "Assignment",
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

            "assignment_id",

            "student_class_id",

            name="uq_assignment_result"

        ),

        Index(

            "idx_assignment_result",

            "student_class_id",

            "is_checked"

        ),

    )


