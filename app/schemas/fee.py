# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import date
from decimal import Decimal
from typing import TypeVar

from pydantic import Field

from app.core.enums import FeeStatus

from .common import (
    ActiveSchema,
    BaseSchema,
    TimestampSchema,
)
from .teacher_student_links import StudentClassResponse

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# FeeBase
# ============================================================


class FeeBase(BaseSchema):
    fee_id: str | None = Field(None, max_length=30)
    fee_month: int = Field(..., ge=1, le=12)
    fee_year: int = Field(..., ge=2000, le=2100)
    total_amount: Decimal
    paid_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    fine_amount: Decimal = Decimal("0.00")
    due_date: date
    paid_date: date | None = None
    status: FeeStatus = FeeStatus.PENDING
    remarks: str | None = None


# ============================================================
# FeeCreate
# ============================================================


class FeeCreate(FeeBase):
    academic_sessions_id: str
    student_class_id: int
    created_by: int


# ============================================================
# FeeResponse
# ============================================================


class FeeResponse(FeeBase, TimestampSchema, ActiveSchema):
    fee_code: str
    academic_sessions_id: str
    student_class_id: str
    created_by: str
    updated_by: str | None = None
    deleted_by: str | None = None

    student_class: StudentClassResponse | None = None


# ============================================================
# FeeUpdate
# ============================================================


class FeeUpdate(BaseSchema):
    fee_month: int | None = Field(None, ge=1, le=12)
    fee_year: int | None = Field(None, ge=2000, le=2100)
    total_amount: Decimal | None = None
    paid_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    fine_amount: Decimal | None = None
    due_date: date | None = None
    paid_date: date | None = None
    status: FeeStatus | None = None
    remarks: str | None = None
    is_active: bool | None = None


# ============================================================
# FeePaymentCreate
# ============================================================


class FeePaymentCreate(BaseSchema):
    amount_paid: Decimal
    payment_date: date
    remarks: str | None = None


# ============================================================
# FeePaymentResponse
# ============================================================


class FeePaymentResponse(BaseSchema):
    id: int
    fee_id: int
    amount_paid: Decimal
    payment_date: date
    remarks: str | None = None


# ============================================================
# FeeSummaryResponse
# ============================================================


class FeeSummaryResponse(BaseSchema):
    student_id: str
    student_name: str
    classroom: str
    total_fee: float
    paid_fee: float
    pending_fee: float
    discount_fee: float
    fine_fee: float
    status: str
