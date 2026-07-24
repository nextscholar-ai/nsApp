from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.core.constants import MAX_CODE_LENGTH
from app.core.mixins import ActiveMixin, AuditMixin, TimestampMixin

# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# ACADEMICSESSION TABLE
# ============================================================


class AcademicSession(Base, TimestampMixin, ActiveMixin, AuditMixin):
    __tablename__ = "academic_sessions"

    session_code = Column(String(MAX_CODE_LENGTH), primary_key=True)

    session_name = Column(String(20), unique=True, nullable=False)

    start_year = Column(Integer, nullable=False)

    end_year = Column(Integer, nullable=False)

    start_date = Column(Date, nullable=False)

    end_date = Column(Date, nullable=False)

    is_current = Column(Boolean, default=False, nullable=False, index=True)

    description = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("end_year > start_year", name="ck_session_year"),
        Index("idx_session_name", "session_name"),
        Index("idx_session_active", "is_current"),
        UniqueConstraint("session_name", name="uq_session_name"),
    )

    classroom = relationship(
        "ClassRoom",
        back_populates="academic_sessions",
        cascade="all, delete-orphan",
    )

    class_subjects = relationship(
        "ClassSubject",
        back_populates="academic_sessions",
        cascade="all, delete-orphan",
    )

    teacher_subjects = relationship(
        "TeacherSubject",
        back_populates="academic_sessions",
        cascade="all, delete-orphan",
    )

    student_classes = relationship(
        "StudentClass",
        back_populates="academic_sessions",
        cascade="all, delete-orphan",
    )

    timetable_entries = relationship(
        "ClassTimeTable",
        back_populates="academic_sessions",
    )

    teacher_availability = relationship(
        "TeacherAvailability",
        back_populates="academic_sessions",
    )

    from_session_promotions = relationship(
        "StudentPromotionHistory",
        foreign_keys="StudentPromotionHistory.from_session_id",
        back_populates="from_session",
    )
    to_session_promotions = relationship(
        "StudentPromotionHistory",
        foreign_keys="StudentPromotionHistory.to_session_id",
        back_populates="to_session",
    )
