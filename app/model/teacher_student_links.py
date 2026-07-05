import uuid
import secrets

from sqlalchemy import Enum

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
# TEACHERSUBJECT TABLE
# ============================================================

class TeacherSubject(Base, TimestampMixin, ActiveMixin):

    __tablename__ = "teacher_subjects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    academic_sessions_id = Column(
        Integer,
        ForeignKey(
            "academic_sessions.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    class_subject_id = Column(
        Integer,
        ForeignKey("class_subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    classroom_id = Column(
        Integer,
        ForeignKey(
            "classroom.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    subject_id = Column(
        Integer,
        ForeignKey(
            "subjects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    teacher_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey(
            "teacher_profiles.teacher_id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    is_class_teacher = Column(
        Boolean,
        default=False,
        nullable=False
    )

    remarks = Column(
        String(300),
        nullable=True
    )

    academic_sessions = relationship(
        "AcademicSession",
        back_populates="teacher_subjects"
    )

    classroom = relationship(
        "ClassRoom",
        back_populates="teacher_subjects"
    )

    subject = relationship(
        "Subject",
        back_populates="teacher_subjects"
    )

    class_subject = relationship(
        "ClassSubject",
        back_populates="teacher_subjects"
    )

    teacher = relationship(
        "TeacherProfile",
        back_populates="teacher_subjects"
    )

    timetable_entries = relationship(
        "ClassTimeTable",
        back_populates="teacher_subject"
    )

    availability_slots = relationship(
        "TeacherAvailability",
        back_populates="teacher_subject",
        cascade="all, delete-orphan"
    )


    __table_args__ = (

        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "subject_id",
            name="uq_teacher_subject"
        ),

        Index(
            "idx_teacher_subject_teacher",
            "teacher_id"
        ),

        Index(
            "idx_teacher_subject_class",
            "classroom_id"
        ),

        Index(
            "idx_teacher_subject_subject",
            "subject_id"
        ),
    )


# ============================================================
# STUDENTCLASS TABLE
# ============================================================

class StudentClass(Base, TimestampMixin, ActiveMixin):

    __tablename__ = "student_classes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # -------------------------
    # Academic Session
    # -------------------------

    academic_sessions_id = Column(
        Integer,
        ForeignKey(
            "academic_sessions.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    # -------------------------
    # Student
    # -------------------------

    student_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey(
            "student_profiles.student_id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # -------------------------
    # Class
    # -------------------------

    classroom_id = Column(
        Integer,
        ForeignKey(
            "classroom.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    # -------------------------
    # Roll Number
    # Session Wise
    # -------------------------

    roll_number = Column(
        Integer,
        nullable=False,
        index=True
    )

    # -------------------------
    # Admission Date
    # -------------------------

    admission_date = Column(
        Date,
        nullable=False
    )

    # -------------------------
    # Student Status
    # -------------------------

    status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
        index=True
    )

    roll_number_locked = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # -------------------------
    # Optional Remarks
    # -------------------------

    remarks = Column(
        String(500),
        nullable=True
    )

    # -------------------------
    # Relationships
    # -------------------------

    student = relationship(
        "StudentProfile",
        back_populates="student_class"
    )

    classroom = relationship(
        "ClassRoom",
        back_populates="student_classes"
    )

    academic_sessions = relationship(
        "AcademicSession",
        back_populates="student_classes"
    )

    # -------------------------
    # Constraints
    # -------------------------

    __table_args__ = (

        # Student can appear only once
        # in one academic session
        UniqueConstraint(
            "academic_sessions_id",
            "student_id",
            name="uq_student_session"
        ),

        # Roll number unique inside class
        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "roll_number",
            name="uq_roll_class"
        ),

        Index(
            "idx_studentclass_student",
            "student_id"
        ),

        Index(
            "idx_studentclass_roll",
            "roll_number"
        ),

        Index(
            "idx_studentclass_class",
            "classroom_id"
        ),

        Index(
            "idx_studentclass_session",
            "academic_sessions_id"
        ),

        Index(
            "idx_studentclass_status",
            "status"
        ),
    )


# ============================================================
# STUDENTPROMOTIONHISTORY TABLE
# ============================================================

class StudentPromotionHistory(
    Base,
    TimestampMixin
):

    __tablename__ = "student_promotion_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    student_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey(
            "student_profiles.student_id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    from_session_id = Column(
        Integer,
        ForeignKey(
            "academic_sessions.id"
        ),
        nullable=False
    )

    to_session_id = Column(
        Integer,
        ForeignKey(
            "academic_sessions.id"
        ),
        nullable=False
    )

    from_classroom_id = Column(
        Integer,
        ForeignKey(
            "classroom.id"
        ),
        nullable=False
    )

    to_classroom_id = Column(
        Integer,
        ForeignKey(
            "classroom.id"
        ),
        nullable=False
    )

    previous_roll_number = Column(
        Integer,
        nullable=False
    )

    new_roll_number = Column(
        Integer,
        nullable=False
    )

    promotion_date = Column(
        Date,
        nullable=False
    )

    promotion_type = Column(
        String(30),
        nullable=False,
        default="PROMOTED"
    )

    remarks = Column(
        String(500)
    )

    promoted_by_user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    student = relationship(
        "StudentProfile",
        back_populates="promotion_history"
    )

    promoted_by = relationship(
        "User"
    )

    from_session = relationship(
        "AcademicSession",
        foreign_keys=[from_session_id]
    )

    to_session = relationship(
        "AcademicSession",
        foreign_keys=[to_session_id]
    )

    from_classroom = relationship(
        "ClassRoom",
        foreign_keys=[from_classroom_id]
    )

    to_classroom = relationship(
        "ClassRoom",
        foreign_keys=[to_classroom_id]
    )

    __table_args__ = (

        Index(
            "idx_student_promotion_student",
            "student_id"
        ),

        Index(
            "idx_student_promotion_date",
            "promotion_date"
        ),
    )


