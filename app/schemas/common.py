from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.enums import UserRole

if TYPE_CHECKING:
    from app.schemas.user import UserResponse


# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")


# ============================================================
# BaseSchema
# ============================================================


class BaseSchema(BaseModel):
    """Base schema with common configurations for Pydantic V2."""

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
            time: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else 0.0,
        },
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
    }


# ============================================================
# TimestampSchema
# ============================================================


class TimestampSchema(BaseSchema):
    """Reflecting TimestampMixin."""

    created_at: datetime | None = None
    updated_at: datetime | None = None


# ============================================================
# ActiveSchema
# ============================================================


class ActiveSchema(BaseSchema):
    """Reflecting ActiveMixin."""

    is_active: bool = True


# ============================================================
# AuditSchema
# ============================================================


class AuditSchema(BaseSchema):
    """Reflecting AuditMixin."""

    created_by: str | None = None
    updated_by: str | None = None


# ============================================================
# UserMinResponse
# ============================================================


class UserMinResponse(ActiveSchema):
    user_code: str
    email: str
    phone: str
    role: UserRole


# ============================================================
# StudentProfileMinResponse
# ============================================================


class StudentProfileMinResponse(ActiveSchema):
    student_id: str
    student_name: str | None = None
    admission_number: str | None = None
    gender: str | None = None


# ============================================================
# TeacherProfileMinResponse
# ============================================================


class TeacherProfileMinResponse(ActiveSchema):
    teacher_id: str
    teacher_name: str | None = None
    employee_code: str | None = None
    designation: str | None = None


# ============================================================
# ClassRoomMinResponse
# ============================================================


class ClassRoomMinResponse(ActiveSchema):
    class_code: str
    class_name: str
    section: str
    display_name: str


# ============================================================
# SubjectMinResponse
# ============================================================


class SubjectMinResponse(ActiveSchema):
    subject_code: str
    subject_name: str
    subject_type: str


# ============================================================
# AcademicSessionMinResponse
# ============================================================


class AcademicSessionMinResponse(ActiveSchema):
    session_code: str
    session_name: str
    is_current: bool


# ============================================================
# ResponseSchema
# ============================================================


class ResponseSchema(BaseSchema, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# PaginatedResponseSchema
# ============================================================


class PaginatedResponseSchema(BaseSchema, Generic[T]):
    success: bool = True
    data: list[T]
    pagination: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# LoginRequest
# ============================================================


class LoginRequest(BaseSchema):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")

    @field_validator("email")
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
    user: UserResponse


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class RefreshTokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(3600, description="Token expiry in seconds")


class LogoutRequest(BaseSchema):
    refresh_token: str | None = None
    device_token: str | None = None
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
