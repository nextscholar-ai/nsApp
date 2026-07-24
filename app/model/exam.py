from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.core.constants import MAX_CODE_LENGTH
from app.core.enums import ExamStatus
from app.core.mixins import ActiveMixin, TimestampMixin
from app.helpers.code_generators import generate_exam_code, generate_exam_result_code

# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# EXAM TABLE
# ============================================================


class Exam(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "exams"

    exam_code = Column(String(30), primary_key=True, default=generate_exam_code)

    # =====================================================
    # Academic
    # =====================================================

    academic_sessions_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("academic_sessions.session_code"),
        nullable=False,
        index=True,
    )

    classroom_id = Column(
        String(30),
        ForeignKey("classroom.class_code"),
        nullable=False,
        index=True,
    )

    class_subject_id = Column(
        String(30),
        ForeignKey("class_subjects.class_subject_code"),
        nullable=False,
        index=True,
    )

    teacher_subject_id = Column(
        String(30),
        ForeignKey("teacher_subjects.teacher_subject_code"),
        nullable=False,
        index=True,
    )

    # =====================================================
    # Exam Details
    # =====================================================

    exam_name = Column(String(150), nullable=False)

    exam_type = Column(String(50), nullable=False)

    description = Column(Text)

    exam_date = Column(Date, nullable=False, index=True)

    start_time = Column(Time)

    end_time = Column(Time)

    duration_minutes = Column(Integer)

    room_number = Column(String(50))

    # =====================================================
    # Marks
    # =====================================================

    total_marks = Column(Float, nullable=False)

    passing_marks = Column(Float, nullable=False)

    # =====================================================
    # Status
    # =====================================================

    status = Column(
        SAEnum(ExamStatus),
        default=ExamStatus.DRAFT,
        nullable=False,
        index=True,
    )

    publish_at = Column(DateTime)

    completed_at = Column(DateTime)

    # =====================================================
    # Statistics
    # =====================================================

    total_students = Column(Integer, default=0)

    result_uploaded = Column(Integer, default=0)

    # =====================================================
    # Audit
    # =====================================================

    created_by = Column(String(30), ForeignKey("users.user_code"), nullable=False)

    updated_by = Column(String(30), ForeignKey("users.user_code"))

    deleted_by = Column(String(30), ForeignKey("users.user_code"))

    # =====================================================
    # Relationships
    # =====================================================

    academic_sessions = relationship("AcademicSession")

    classroom = relationship("ClassRoom")

    class_subject = relationship("ClassSubject")

    teacher_subject = relationship("TeacherSubject")

    creator = relationship("User", foreign_keys=[created_by])

    updater = relationship("User", foreign_keys=[updated_by])

    deleter = relationship("User", foreign_keys=[deleted_by])

    results = relationship(
        "ExamResult",
        back_populates="exam",
        cascade="all, delete-orphan",
    )

    # =====================================================
    # Constraints
    # =====================================================

    __table_args__ = (
        UniqueConstraint("class_subject_id", "exam_name", "exam_date", name="uq_exam"),
        Index("idx_exam_class", "classroom_id", "exam_date"),
        Index("idx_exam_teacher", "teacher_subject_id", "status"),
    )


# ============================================================
# EXAMRESULT TABLE
# ============================================================


class ExamResult(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "exam_results"

    exam_result_code = Column(String(30), primary_key=True, default=generate_exam_result_code)

    exam_id = Column(
        String(30),
        ForeignKey("exams.exam_code"),
        nullable=False,
        index=True,
    )

    student_class_id = Column(
        String(30),
        ForeignKey("student_classes.student_class_code"),
        nullable=False,
        index=True,
    )

    obtained_marks = Column(Float, nullable=False, default=0)

    percentage = Column(Float, default=0)

    grade = Column(String(10))

    remarks = Column(Text)

    rank_in_class = Column(Integer)

    is_absent = Column(Boolean, default=False)

    checked_by = Column(String(30), ForeignKey("users.user_code"))

    checked_at = Column(DateTime)

    exam = relationship("Exam", back_populates="results")

    student_class = relationship("StudentClass")

    checker = relationship("User")

    __table_args__ = (
        UniqueConstraint("exam_id", "student_class_id", name="uq_exam_result"),
        Index("idx_exam_result", "student_class_id", "exam_id"),
        Index("idx_exam_rank", "exam_id", "rank_in_class"),
    )
