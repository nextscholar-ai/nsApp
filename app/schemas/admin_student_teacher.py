from pydantic import EmailStr, Field

from .common import BaseSchema, PaginatedResponseSchema


class TeacherAdminListResponse(BaseSchema):
    user_id: str
    teacher_id: str
    teacher_name: str
    email: EmailStr
    phone: str
    designation: str | None = None
    department: str | None = None
    assigned_classes: list[str] = Field(default_factory=list)
    status: str | None = None


class StudentAdminListResponse(BaseSchema):
    user_id: str
    student_id: str
    student_name: str
    class_: str | None = None
    section: str | None = None
    email: EmailStr
    phone: str
    status: str | None = None


class PaginatedTeacherAdminListResponse(
    PaginatedResponseSchema[TeacherAdminListResponse],
):
    pass


class PaginatedStudentAdminListResponse(
    PaginatedResponseSchema[StudentAdminListResponse],
):
    pass
