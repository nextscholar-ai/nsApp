from datetime import date
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.core.mixins import TimestampMixin, ActiveMixin, AuditMixin


class StudentIDCard(Base, TimestampMixin, ActiveMixin, AuditMixin):
    """Stores the generated artifacts for a student's ID card (front side only)."""

    __tablename__ = "student_id_cards"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Student
    student_id = Column(
        String(30),
        ForeignKey("student_profiles.student_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session-wise validity
    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Snapshot of student/session details for PDF rendering
    student_name = Column(String(120), nullable=False)
    parent_name = Column(String(120), nullable=True)
    class_display_name = Column(String(150), nullable=True)

    institute_name = Column(String(255), nullable=False)
    institute_contact_number = Column(String(30), nullable=False)
    academic_session_label = Column(String(120), nullable=True)

    date_of_joining = Column(Date, nullable=True)
    valid_till = Column(Date, nullable=True)

    # File paths under /uploads
    institute_logo_path = Column(String(500), nullable=True)
    student_photo_path = Column(String(500), nullable=True)

    qr_code_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)

    # business identifiers snapshot
    student_id_business = Column(String(30), nullable=False)

    # relationships
    student = relationship("StudentProfile")

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_sessions_id",
            name="uq_student_idcard_student_session",
        ),
        Index("idx_student_id_cards_student", "student_id"),
        Index("idx_student_id_cards_session", "academic_sessions_id"),
    )

