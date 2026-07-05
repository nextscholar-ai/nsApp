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


# ============================================================
# BaseSchema
# ============================================================

class BaseSchema(BaseModel):
    """Base schema with common configurations for Pydantic V2"""
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
            time: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else 0.0
        },
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "populate_by_name": True
    }


# ============================================================
# TimestampSchema
# ============================================================

class TimestampSchema(BaseSchema):
    """Reflecting TimestampMixin"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# ActiveSchema
# ============================================================

class ActiveSchema(BaseSchema):
    """Reflecting ActiveMixin"""
    is_active: bool = True


# ============================================================
# AuditSchema
# ============================================================

class AuditSchema(BaseSchema):
    """Reflecting AuditMixin"""
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


# ============================================================
# UserMinResponse
# ============================================================

class UserMinResponse(ActiveSchema):
    id: int
    email: str
    phone: str
    role: UserRole


# ============================================================
# StudentProfileMinResponse
# ============================================================

class StudentProfileMinResponse(ActiveSchema):
    student_id: str
    student_name:Optional[str]=None
    admission_number: Optional[str] = None
    gender: Optional[str] = None


# ============================================================
# TeacherProfileMinResponse
# ============================================================

class TeacherProfileMinResponse(ActiveSchema):
    teacher_id: str
    teacher_name: Optional[str]=None
    employee_code: Optional[str] = None
    designation: Optional[str] = None


# ============================================================
# ClassRoomMinResponse
# ============================================================

class ClassRoomMinResponse(ActiveSchema):
    id: int
    class_code: str
    class_name: str
    section: str
    display_name: str


# ============================================================
# SubjectMinResponse
# ============================================================

class SubjectMinResponse(ActiveSchema):
    id: int
    subject_code: str
    subject_name: str
    subject_type: str


# ============================================================
# AcademicSessionMinResponse
# ============================================================

class AcademicSessionMinResponse(ActiveSchema):
    id: int
    session_code: str
    session_name: str
    is_current: bool


# ============================================================
# ResponseSchema
# ============================================================

class ResponseSchema(BaseSchema, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# PaginatedResponseSchema
# ============================================================

class PaginatedResponseSchema(BaseSchema, Generic[T]):
    success: bool = True
    data: List[T]
    pagination: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# LoginRequest
# ============================================================

class LoginRequest(BaseSchema):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: EmailStr) -> EmailStr:
        return v.lower().strip()


# ============================================================
# LoginResponse
# ============================================================

class LoginResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(3600, description="Token expiry in seconds")
    user: 'UserResponse'


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class RefreshTokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(3600, description="Token expiry in seconds")


class LogoutRequest(BaseSchema):
    refresh_token: Optional[str] = None
    device_token: Optional[str] = None
    all_devices: bool = False


class ChangePasswordRequest(BaseSchema):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseSchema):
    email: EmailStr


class ResetPasswordRequest(BaseSchema):
    token: str
    new_password: str = Field(..., min_length=8)


class VerifyEmailRequest(BaseSchema):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class ResendOTPRequest(BaseSchema):
    email: EmailStr

