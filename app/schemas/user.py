# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import date, datetime
from typing import Optional, TypeVar

from pydantic import EmailStr, Field, field_validator

from app.core.enums import UserRole

from .common import (
    ActiveSchema,
    AuditSchema,
    BaseSchema,
    StudentProfileMinResponse,
    TeacherProfileMinResponse,
    TimestampSchema,
    UserMinResponse,
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# UserBase
# ============================================================


class UserBase(BaseSchema):
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    role: UserRole

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = "".join(filter(str.isdigit, v))
        if len(v) < 10 or len(v) > 15:
            msg = "Phone number must be between 10 and 15 digits"
            raise ValueError(msg)
        return v


# ============================================================
# UserCreate
# ============================================================


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


# ============================================================
# UserUpdate
# ============================================================


class UserUpdate(BaseSchema):
    email: EmailStr | None = None
    phone: str | None = Field(None, min_length=10, max_length=15)
    profile_photo: str | None = None
    is_active: bool | None = None
    device_token: str | None = None


# ============================================================
# UserResponse
# ============================================================


class UserResponse(TimestampSchema, ActiveSchema, AuditSchema):
    email: str
    phone: str
    role: UserRole
    user_code: str
    admin_id: str | None = None
    teacher_id: str | None = None
    student_id: str | None = None
    profile_photo: str | None = None
    last_seen: datetime | None = None
    device_token: str | None = None
    email_verified: bool = False
    last_login: datetime | None = None
    login_count: int = 0
    failed_login_count: int = 0
    is_deleted: bool = False

    student_profile: StudentProfileMinResponse | None = None
    teacher_profile: TeacherProfileMinResponse | None = None
    admin_profile: Optional["AdminProfileResponse"] = None


# ============================================================
# StudentProfileBase
# ============================================================


class StudentProfileBase(BaseSchema):
    student_name: str = Field(..., min_length=1, max_length=255)
    gender: str | None = Field(None, max_length=20)
    date_of_birth: date | None = None
    blood_group: str | None = Field(None, max_length=10)
    profile_photo: str | None = None
    school_name: str = Field("", max_length=255)
    school_address: str | None = None
    medium: str | None = Field(None, max_length=100)
    board: str | None = Field(None, max_length=100)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    parent_name: str | None = Field(None, max_length=255)
    parent_phone: str | None = Field(None, min_length=10, max_length=15)
    guardian_name: str | None = Field(None, max_length=255)
    guardian_phone: str | None = Field(None, min_length=10, max_length=15)
    emergency_contact: str | None = Field(None, min_length=10, max_length=15)
    admission_date: date | None = None
    remarks: str | None = None


# ============================================================
# StudentProfileCreate
# ============================================================


class StudentProfileCreate(StudentProfileBase):
    user_id: str
    student_id: str
    admission_number: str | None = None
    # registration_number is intentionally NOT accepted on create —
    # it's always system-generated (see RegistrationNumberService).


# ============================================================
# StudentProfileUpdate
# ============================================================


class StudentProfileUpdate(StudentProfileBase):
    pass


# ============================================================
# StudentProfileResponse
# ============================================================


class StudentProfileResponse(
    StudentProfileBase,
    TimestampSchema,
    ActiveSchema,
    AuditSchema,
):
    student_id: str
    user_id: str
    admission_number: str | None = None
    registration_number: str | None = None
    user: UserMinResponse | None = None


# ============================================================
# TeacherProfileBase
# ============================================================


class TeacherProfileBase(BaseSchema):
    teacher_name: str = Field(..., min_length=1, max_length=255)
    gender: str | None = Field(None, max_length=20)
    date_of_birth: date | None = None
    qualification: str | None = Field(None, max_length=255)
    experience_years: float | None = 0.0
    specialization: str | None = Field(None, max_length=255)
    profile_photo: str | None = None
    employee_code: str | None = Field(None, max_length=30)
    joining_date: date | None = None
    designation: str | None = Field(None, max_length=100)
    department: str | None = Field(None, max_length=100)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    emergency_contact: str | None = Field(None, min_length=10, max_length=15)
    remarks: str | None = None


# ============================================================
# TeacherProfileCreate
# ============================================================


class TeacherProfileCreate(TeacherProfileBase):
    user_id: str
    teacher_id: str


# ============================================================
# TeacherProfileUpdate
# ============================================================


class TeacherProfileUpdate(TeacherProfileBase):
    pass


# ============================================================
# TeacherProfileResponse
# ============================================================


class TeacherProfileResponse(
    TeacherProfileBase,
    TimestampSchema,
    ActiveSchema,
    AuditSchema,
):
    teacher_id: str
    user_id: str
    user: UserMinResponse | None = None


# ============================================================
# AdminProfileBase
# ============================================================


class AdminProfileBase(BaseSchema):
    admin_name: str = Field(..., min_length=1, max_length=120)
    designation: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, min_length=10, max_length=20)
    profile_photo: str | None = None
    notes: str | None = None
    can_create_admin: bool = False
    super_admin: bool = False


# ============================================================
# AdminProfileCreate
# ============================================================


class AdminProfileCreate(AdminProfileBase):
    user_id: str
    admin_id: str | None = None


# ============================================================
# AdminProfileUpdate
# ============================================================


class AdminProfileUpdate(AdminProfileBase):
    pass


# ============================================================
# AdminProfileResponse
# ============================================================


class AdminProfileResponse(AdminProfileBase, TimestampSchema, ActiveSchema):
    admin_id: str
    user_id: str
    user: UserMinResponse | None = None
