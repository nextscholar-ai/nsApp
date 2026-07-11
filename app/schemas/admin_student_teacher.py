from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .common import BaseSchema, PaginatedResponseSchema


class TeacherAdminListResponse(BaseSchema):
    user_id: int
    teacher_id: str
    teacher_name: str
    email: EmailStr
    phone: str
    designation: Optional[str] = None
    department: Optional[str] = None
    assigned_classes: List[str] = Field(default_factory=list)
    status: Optional[str] = None


class StudentAdminListResponse(BaseSchema):
    user_id: int
    student_id: str
    student_name: str
    class_: Optional[str] = None
    section: Optional[str] = None
    email: EmailStr
    phone: str
    status: Optional[str] = None


class PaginatedTeacherAdminListResponse(PaginatedResponseSchema[TeacherAdminListResponse]):
    pass


class PaginatedStudentAdminListResponse(PaginatedResponseSchema[StudentAdminListResponse]):
    pass

