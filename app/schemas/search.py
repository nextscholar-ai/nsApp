# ============================================================
# app/schemas/search.py
# ============================================================
#
# Response formatting layer: the shape every search endpoint returns.
# Kept intentionally consistent between Student and Teacher search so
# frontend code can treat them the same way. `internal_id` is always
# present but explicitly documented as internal - the business ID
# (student_id/teacher_id), never the numeric primary key.

from typing import List, Optional
from pydantic import BaseModel, Field


class StudentSearchResultItem(BaseModel):
    display_name: str = Field(..., description="Student's full name, for display only")
    email: Optional[str] = None
    student_code: str = Field(..., description="Human-facing code (admission number)")
    internal_id: str = Field(..., description="Internal identifier (student_id) - use this in follow-up API calls")

    registration_number: Optional[str] = None
    phone: Optional[str] = None
    profile_photo: Optional[str] = None

    score: float = Field(..., description="Blended confidence, 0-100")
    confidence_label: str = Field(..., description='"high" | "medium" | "low"')
    match_type: str = Field(..., description='"exact" | "fuzzy"')
    matched_field: str
    signals: List[str] = Field(default_factory=list, description='e.g. ["exact:email", "fuzzy:student_name"]')


class StudentSearchResponse(BaseModel):
    query: str
    query_type: str = Field(..., description='"email" | "name_or_code", auto-detected')
    result_count: int
    results: List[StudentSearchResultItem]


class TeacherSearchResultItem(BaseModel):
    display_name: str
    email: Optional[str] = None
    teacher_code: str = Field(..., description="Human-facing code (employee code)")
    internal_id: str = Field(..., description="Internal identifier (teacher_id) - use this in follow-up API calls")

    department: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    profile_photo: Optional[str] = None

    score: float
    confidence_label: str
    match_type: str
    matched_field: str
    signals: List[str] = Field(default_factory=list)


class TeacherSearchResponse(BaseModel):
    query: str
    query_type: str
    result_count: int
    results: List[TeacherSearchResultItem]
