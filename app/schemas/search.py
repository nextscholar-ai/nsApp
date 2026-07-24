from datetime import date

from pydantic import BaseModel, Field


class StudentSearchDetail(BaseModel):
    student_id: str = Field(
        ...,
        description="Unique student identifier - use this in follow-up API calls",
    )
    admission_number: str | None = None
    registration_number: str | None = None
    student_name: str
    gender: str | None = None
    date_of_birth: date | None = None
    blood_group: str | None = None
    profile_photo: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    parent_name: str | None = None
    parent_phone: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    emergency_contact: str | None = None
    admission_date: date | None = None
    school_name: str | None = None
    medium: str | None = None
    board: str | None = None
    remarks: str | None = None
    email: str | None = None
    phone: str | None = None
    user_id: str | None = None
    is_active: bool | None = None

    class_id: str | None = None
    class_name: str | None = None
    section: str | None = None
    display_name: str | None = None
    roll_number: int | None = None

    score: float = Field(..., description="Blended confidence, 0-100")
    confidence_label: str = Field(..., description='"high" | "medium" | "low"')
    match_type: str = Field(..., description='"exact" | "fuzzy"')
    matched_field: str
    signals: list[str] = Field(
        default_factory=list,
        description='e.g. ["exact:email", "fuzzy:student_name"]',
    )


class TeacherSearchDetail(BaseModel):
    teacher_id: str = Field(
        ...,
        description="Unique teacher identifier - use this in follow-up API calls",
    )
    employee_code: str | None = None
    teacher_name: str
    gender: str | None = None
    date_of_birth: date | None = None
    qualification: str | None = None
    experience_years: float | None = None
    specialization: str | None = None
    profile_photo: str | None = None
    joining_date: date | None = None
    designation: str | None = None
    department: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    emergency_contact: str | None = None
    remarks: str | None = None
    email: str | None = None
    phone: str | None = None
    user_id: str | None = None
    is_active: bool | None = None

    subjects: list[str] = Field(
        default_factory=list,
        description="Subject names taught by the teacher",
    )
    class_teacher_of: str | None = None

    score: float
    confidence_label: str
    match_type: str
    matched_field: str
    signals: list[str] = Field(default_factory=list)


class StudentSearchResponse(BaseModel):
    query: str
    query_type: str = Field(..., description='"email" | "name_or_code", auto-detected')
    result_count: int
    results: list[StudentSearchDetail]


class TeacherSearchResponse(BaseModel):
    query: str
    query_type: str
    result_count: int
    results: list[TeacherSearchDetail]
