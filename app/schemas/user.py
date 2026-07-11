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


# ============================================================
# UserBase
# ============================================================

class UserBase(BaseSchema):
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    role: UserRole

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = ''.join(filter(str.isdigit, v))
        if len(v) < 10 or len(v) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
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
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    profile_photo: Optional[str] = None
    is_active: Optional[bool] = None
    device_token: Optional[str] = None


# ============================================================
# UserResponse
# ============================================================

class UserResponse(TimestampSchema, ActiveSchema, AuditSchema):
    email: str
    phone: str
    role: UserRole
    id: int
    admin_id: Optional[str] = None
    teacher_id: Optional[str] = None
    student_id: Optional[str] = None
    profile_photo: Optional[str] = None
    last_seen: Optional[datetime] = None
    device_token: Optional[str] = None
    email_verified: bool = False
    last_login: Optional[datetime] = None
    login_count: int = 0
    failed_login_count: int = 0
    is_deleted: bool = False
    
    student_profile: Optional[StudentProfileMinResponse] = None
    teacher_profile: Optional[TeacherProfileMinResponse] = None
    admin_profile: Optional['AdminProfileResponse'] = None


# ============================================================
# StudentProfileBase
# ============================================================

class StudentProfileBase(BaseSchema):
    student_name: str = Field(..., min_length=1, max_length=255)
    gender: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = Field(None, max_length=10)
    profile_photo: Optional[str] = None
    school_name: str = Field("", max_length=255)
    school_address: Optional[str] = None
    medium: Optional[str] = Field(None, max_length=100)
    board: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    parent_name: Optional[str] = Field(None, max_length=255)
    parent_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    guardian_name: Optional[str] = Field(None, max_length=255)
    guardian_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    emergency_contact: Optional[str] = Field(None, min_length=10, max_length=15)
    admission_date: Optional[date] = None
    remarks: Optional[str] = None


# ============================================================
# StudentProfileCreate
# ============================================================

class StudentProfileCreate(StudentProfileBase):
    user_id: int
    student_id: str
    admission_number: Optional[str] = None
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

class StudentProfileResponse(StudentProfileBase, TimestampSchema, ActiveSchema, AuditSchema):
    student_id: str
    user_id: int
    admission_number: Optional[str] = None
    registration_number: Optional[str] = None
    user: Optional[UserMinResponse] = None


# ============================================================
# TeacherProfileBase
# ============================================================

class TeacherProfileBase(BaseSchema):
    teacher_name: str = Field(..., min_length=1, max_length=255)
    gender: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    qualification: Optional[str] = Field(None, max_length=255)
    experience_years: Optional[float] = 0.0
    specialization: Optional[str] = Field(None, max_length=255)
    profile_photo: Optional[str] = None
    employee_code: Optional[str] = Field(None, max_length=30)
    joining_date: Optional[date] = None
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    emergency_contact: Optional[str] = Field(None, min_length=10, max_length=15)
    remarks: Optional[str] = None


# ============================================================
# TeacherProfileCreate
# ============================================================

class TeacherProfileCreate(TeacherProfileBase):
    user_id: int
    teacher_id: str


# ============================================================
# TeacherProfileUpdate
# ============================================================

class TeacherProfileUpdate(TeacherProfileBase):
    pass


# ============================================================
# TeacherProfileResponse
# ============================================================

class TeacherProfileResponse(TeacherProfileBase, TimestampSchema, ActiveSchema, AuditSchema):
    teacher_id: str
    user_id: int
    user: Optional[UserMinResponse] = None


# ============================================================
# AdminProfileBase
# ============================================================

class AdminProfileBase(BaseSchema):
    admin_name: str = Field(..., min_length=1, max_length=120)
    designation: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    profile_photo: Optional[str] = None
    notes: Optional[str] = None
    can_create_admin: bool = False
    super_admin: bool = False


# ============================================================
# AdminProfileCreate
# ============================================================

class AdminProfileCreate(AdminProfileBase):
    user_id: int
    admin_id: Optional[str] = None


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
    user_id: int
    user: Optional[UserMinResponse] = None

