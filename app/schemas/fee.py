# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional, Generic, TypeVar, List, Dict, Any, Union
from datetime import datetime, date, time
from decimal import Decimal
from  enum import Enum

from app.core.enums import (
    UserRole, 
    AssignmentStatus, 
    ExamStatus, 
    FeeStatus,
    NoticeType,
    NoticeAudience,
    MaterialType,
    AttendanceStatus,
    LectureStatus,
    PromotionType,
    Gender
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar('T')


from .common import *
from .teacher_student_links import StudentClassResponse


# ============================================================
# FeeBase
# ============================================================

class FeeBase(BaseSchema):
    fee_id: str = Field(..., max_length=30)
    fee_month: int = Field(..., ge=1, le=12)
    fee_year: int = Field(..., ge=2000, le=2100)
    total_amount: Decimal
    paid_amount: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    fine_amount: Decimal = Decimal('0.00')
    due_date: date
    paid_date: Optional[date] = None
    status: FeeStatus = FeeStatus.PENDING
    remarks: Optional[str] = None


# ============================================================
# FeeCreate
# ============================================================

class FeeCreate(FeeBase):
    academic_sessions_id: int
    student_class_id: int
    created_by: int


# ============================================================
# FeeResponse
# ============================================================

class FeeResponse(FeeBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    student_class_id: int
    created_by: int
    updated_by: Optional[int] = None
    deleted_by: Optional[int] = None
    
    student_class: Optional[StudentClassResponse] = None



# ============================================================
# FeeUpdate
# ============================================================

class FeeUpdate(BaseSchema):
    fee_month: Optional[int] = Field(None, ge=1, le=12)
    fee_year: Optional[int] = Field(None, ge=2000, le=2100)
    total_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    fine_amount: Optional[Decimal] = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    status: Optional[FeeStatus] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================
# FeePaymentCreate
# ============================================================

class FeePaymentCreate(BaseSchema):
    amount_paid: Decimal
    payment_date: date
    remarks: Optional[str] = None


# ============================================================
# FeePaymentResponse
# ============================================================

class FeePaymentResponse(BaseSchema):
    id: int
    fee_id: int
    amount_paid: Decimal
    payment_date: date
    remarks: Optional[str] = None


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
