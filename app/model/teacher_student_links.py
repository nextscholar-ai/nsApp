from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.core.constants import MAX_CODE_LENGTH
from app.core.mixins import ActiveMixin, TimestampMixin
from app.helpers.code_generators import (
    generate_promotion_code,
    generate_student_class_code,
    generate_teacher_subject_code,
)

# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# TEACHERSUBJECT TABLE
# ============================================================


class TeacherSubject(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "teacher_subjects"

    @hybrid_property
    def id(self):
        return self.teacher_subject_code

    @id.expression
    def id(cls):
        return cls.teacher_subject_code

    teacher_subject_code = Column(
        String(30),
        primary_key=True,
        default=generate_teacher_subject_code,
    )

    academic_sessions_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("academic_sessions.session_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    class_subject_id = Column(
        String(30),
        ForeignKey("class_subjects.class_subject_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    classroom_id = Column(
        String(30),
        ForeignKey("classroom.class_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subject_id = Column(
        String(30),
        ForeignKey("subjects.subject_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    teacher_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("teacher_profiles.teacher_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_class_teacher = Column(Boolean, default=False, nullable=False)

    remarks = Column(String(300), nullable=True)

    academic_sessions = relationship(
        "AcademicSession",
        back_populates="teacher_subjects",
    )

    classroom = relationship("ClassRoom", back_populates="teacher_subjects")

    subject = relationship("Subject", back_populates="teacher_subjects")

    class_subject = relationship("ClassSubject", back_populates="teacher_subjects")

    teacher = relationship("TeacherProfile", back_populates="teacher_subjects")

    timetable_entries = relationship("ClassTimeTable", back_populates="teacher_subject")

    availability_slots = relationship(
        "TeacherAvailability",
        back_populates="teacher_subject",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "subject_id",
            name="uq_teacher_subject",
        ),
        Index("idx_teacher_subject_teacher", "teacher_id"),
        Index("idx_teacher_subject_class", "classroom_id"),
        Index("idx_teacher_subject_subject", "subject_id"),
    )


# ============================================================
# STUDENTCLASS TABLE
# ============================================================


class StudentClass(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "student_classes"

    @hybrid_property
    def id(self):
        return self.student_class_code

    @id.expression
    def id(cls):
        return cls.student_class_code

    student_class_code = Column(
        String(30),
        primary_key=True,
        default=generate_student_class_code,
    )

    # -------------------------
    # Academic Session
    # -------------------------

    academic_sessions_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("academic_sessions.session_code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # -------------------------
    # Student
    # -------------------------

    student_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("student_profiles.student_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -------------------------
    # Class
    # -------------------------

    classroom_id = Column(
        String(30),
        ForeignKey("classroom.class_code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # -------------------------
    # Roll Number
    # Session Wise
    # -------------------------

    roll_number = Column(Integer, nullable=False, index=True)

    # -------------------------
    # Admission Date
    # -------------------------

    admission_date = Column(Date, nullable=False)

    # -------------------------
    # Student Status
    # -------------------------

    status = Column(String(30), nullable=False, default="ACTIVE", index=True)

    roll_number_locked = Column(Boolean, default=False, nullable=False)

    # -------------------------
    # Optional Remarks
    # -------------------------

    remarks = Column(String(500), nullable=True)

    # -------------------------
    # Relationships
    # -------------------------

    student = relationship("StudentProfile", back_populates="student_class")

    classroom = relationship("ClassRoom", back_populates="student_classes")

    academic_sessions = relationship(
        "AcademicSession",
        back_populates="student_classes",
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
            name="uq_student_session",
        ),
        # Roll number unique inside class
        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "roll_number",
            name="uq_roll_class",
        ),
        Index("idx_studentclass_student", "student_id"),
        Index("idx_studentclass_roll", "roll_number"),
        Index("idx_studentclass_class", "classroom_id"),
        Index("idx_studentclass_session", "academic_sessions_id"),
        Index("idx_studentclass_status", "status"),
    )


# ============================================================
# STUDENTPROMOTIONHISTORY TABLE
# ============================================================


class StudentPromotionHistory(Base, TimestampMixin):
    __tablename__ = "student_promotion_history"

    promotion_code = Column(
        String(30),
        primary_key=True,
        default=generate_promotion_code,
    )

    student_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("student_profiles.student_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_session_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("academic_sessions.session_code"),
        nullable=False,
    )

    to_session_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("academic_sessions.session_code"),
        nullable=False,
    )

    from_classroom_id = Column(
        String(30),
        ForeignKey("classroom.class_code"),
        nullable=False,
    )

    to_classroom_id = Column(
        String(30),
        ForeignKey("classroom.class_code"),
        nullable=False,
    )

    previous_roll_number = Column(Integer, nullable=False)

    new_roll_number = Column(Integer, nullable=False)

    promotion_date = Column(Date, nullable=False)

    promotion_type = Column(String(30), nullable=False, default="PROMOTED")

    remarks = Column(String(500))

    promoted_by_user_id = Column(String(30), ForeignKey("users.user_code"))

    student = relationship("StudentProfile", back_populates="promotion_history")

    promoted_by = relationship("User", foreign_keys=[promoted_by_user_id])

    from_session = relationship(
        "AcademicSession",
        foreign_keys=[from_session_id],
        back_populates="from_session_promotions",
    )

    to_session = relationship(
        "AcademicSession",
        foreign_keys=[to_session_id],
        back_populates="to_session_promotions",
    )

    from_classroom = relationship(
        "ClassRoom",
        foreign_keys=[from_classroom_id],
        back_populates="from_class_promotions",
    )

    to_classroom = relationship(
        "ClassRoom",
        foreign_keys=[to_classroom_id],
        back_populates="to_class_promotions",
    )

    __table_args__ = (
        Index("idx_student_promotion_student", "student_id"),
        Index("idx_student_promotion_date", "promotion_date"),
    )
