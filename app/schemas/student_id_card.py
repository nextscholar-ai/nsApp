from datetime import date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.schemas.common import BaseSchema


class StudentIDCardGenerateResponse(BaseSchema):
    success: bool
    card_id: int
    student_id: str
    academic_sessions_id: int
    pdf_path: Optional[str] = None
    qr_code_path: Optional[str] = None


class StudentIDCardResponse(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: str
    academic_sessions_id: int

    institute_logo_path: Optional[str] = None
    institute_name: str
    institute_contact_number: str
    academic_session_label: Optional[str] = None

    date_of_joining: Optional[date] = None
    valid_till: Optional[date] = None

    student_photo_path: Optional[str] = None
    student_name: str
    parent_name: Optional[str] = None

    class_display_name: Optional[str] = None
    student_id_business: str

    qr_code_path: Optional[str] = None
    pdf_path: Optional[str] = None


class StudentIDCardDownloadResponse(BaseSchema):
    success: bool
    download_url: str
    pdf_path: str


class PaginatedStudentIDCardListResponse(BaseSchema):
    success: bool
    data: List[StudentIDCardResponse]
    pagination: dict

