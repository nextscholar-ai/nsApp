from datetime import date

from pydantic import ConfigDict

from app.schemas.common import BaseSchema


class StudentIDCardGenerateResponse(BaseSchema):
    success: bool
    card_id: str
    student_id: str
    academic_sessions_id: str
    pdf_path: str | None = None
    qr_code_path: str | None = None


class StudentIDCardResponse(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id_card_code: str
    student_id: str
    academic_sessions_id: str

    institute_logo_path: str | None = None
    institute_name: str
    institute_contact_number: str
    academic_session_label: str | None = None

    date_of_joining: date | None = None
    valid_till: date | None = None

    student_photo_path: str | None = None
    student_name: str
    parent_name: str | None = None

    class_display_name: str | None = None
    student_id_business: str

    qr_code_path: str | None = None
    pdf_path: str | None = None


class StudentIDCardDownloadResponse(BaseSchema):
    success: bool
    download_url: str
    pdf_path: str


class PaginatedStudentIDCardListResponse(BaseSchema):
    success: bool
    data: list[StudentIDCardResponse]
    pagination: dict
