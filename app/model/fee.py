from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.core.constants import MAX_CODE_LENGTH
from app.core.enums import FeeStatus
from app.core.mixins import ActiveMixin, TimestampMixin
from app.helpers.code_generators import generate_fee_code

# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# FEE TABLE
# ============================================================


class Fee(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "fees"

    fee_code = Column(String(30), primary_key=True, default=generate_fee_code)

    # =====================================================
    # Academic
    # =====================================================

    academic_sessions_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("academic_sessions.session_code"),
        nullable=False,
        index=True,
    )

    student_class_id = Column(
        String(30),
        ForeignKey("student_classes.student_class_code"),
        nullable=False,
        index=True,
    )

    # =====================================================
    # Month
    # =====================================================

    fee_month = Column(Integer, nullable=False)

    fee_year = Column(Integer, nullable=False)

    # =====================================================
    # Amount
    # =====================================================

    total_amount = Column(Numeric(10, 2), nullable=False)

    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)

    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)

    fine_amount = Column(Numeric(10, 2), nullable=False, default=0)

    # =====================================================
    # Due
    # =====================================================

    due_date = Column(Date, nullable=False)

    paid_date = Column(Date)

    # =====================================================
    # Status
    # =====================================================

    status = Column(
        SAEnum(FeeStatus),
        nullable=False,
        default=FeeStatus.PENDING,
        index=True,
    )

    remarks = Column(Text)

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

    student_class = relationship("StudentClass")

    creator = relationship("User", foreign_keys=[created_by])

    updater = relationship("User", foreign_keys=[updated_by])

    deleter = relationship("User", foreign_keys=[deleted_by])

    # =====================================================
    # Constraints
    # =====================================================

    __table_args__ = (
        UniqueConstraint(
            "student_class_id",
            "fee_month",
            "fee_year",
            name="uq_student_fee",
        ),
        CheckConstraint("fee_month >=1 AND fee_month<=12", name="ck_fee_month"),
        CheckConstraint("paid_amount>=0", name="ck_paid_amount"),
        CheckConstraint("discount_amount>=0", name="ck_discount_amount"),
        CheckConstraint("fine_amount>=0", name="ck_fine_amount"),
        Index("idx_fee_student", "student_class_id", "status"),
        Index("idx_fee_due", "due_date", "status"),
    )
