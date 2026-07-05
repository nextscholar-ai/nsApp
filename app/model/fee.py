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
# FEE TABLE
# ============================================================

class Fee(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "fees"

    id = Column(
        Integer,
        primary_key=True
    )

    fee_id = Column(

        String(30),

        unique=True,

        nullable=False,

        default=generate_fee_code,

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

    student_class_id = Column(

        Integer,

        ForeignKey(
            "student_classes.id"
        ),

        nullable=False,

        index=True

    )

    # =====================================================
    # Month
    # =====================================================

    fee_month = Column(

        Integer,

        nullable=False

    )

    fee_year = Column(

        Integer,

        nullable=False

    )

    # =====================================================
    # Amount
    # =====================================================

    total_amount = Column(

        Numeric(10,2),

        nullable=False

    )

    paid_amount = Column(

        Numeric(10,2),

        nullable=False,

        default=0

    )

    discount_amount = Column(

        Numeric(10,2),

        nullable=False,

        default=0

    )

    fine_amount = Column(

        Numeric(10,2),

        nullable=False,

        default=0

    )

    # =====================================================
    # Due
    # =====================================================

    due_date = Column(

        Date,

        nullable=False

    )

    paid_date = Column(

        Date

    )

    # =====================================================
    # Status
    # =====================================================

    status = Column(

        SAEnum(FeeStatus),

        nullable=False,

        default=FeeStatus.PENDING,

        index=True

    )

    remarks = Column(

        Text

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

    student_class = relationship(
        "StudentClass"
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

    

    # =====================================================
    # Constraints
    # =====================================================

    __table_args__ = (

        UniqueConstraint(

            "student_class_id",

            "fee_month",

            "fee_year",

            name="uq_student_fee"

        ),

        CheckConstraint(

            "fee_month >=1 AND fee_month<=12",

            name="ck_fee_month"

        ),

        CheckConstraint(

            "paid_amount>=0",

            name="ck_paid_amount"

        ),

        CheckConstraint(

            "discount_amount>=0",

            name="ck_discount_amount"

        ),

        CheckConstraint(

            "fine_amount>=0",

            name="ck_fine_amount"

        ),

        Index(

            "idx_fee_student",

            "student_class_id",

            "status"

        ),

        Index(

            "idx_fee_due",

            "due_date",

            "status"

        ),

    )


