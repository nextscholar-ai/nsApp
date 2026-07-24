from typing import TypeVar

from pydantic import Field

from app.core.enums import MaterialType

from .common import (
    ActiveSchema,
    BaseSchema,
    ClassRoomMinResponse,
    TimestampSchema,
    UserMinResponse,
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# StudyMaterialBase
# ============================================================


class StudyMaterialBase(BaseSchema):
    title: str = Field(..., max_length=200)
    description: str | None = None
    material_type: MaterialType
    file_name: str = Field(..., max_length=255)
    file_url: str = Field(..., max_length=500)
    file_size: int | None = None
    mime_type: str | None = Field(None, max_length=100)
    download_count: int = 0


# ============================================================
# StudyMaterialCreate
# ============================================================


class StudyMaterialCreate(StudyMaterialBase):
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: str
    teacher_subject_id: str
    uploaded_by: str


# ============================================================
# StudyMaterialResponse
# ============================================================


class StudyMaterialResponse(StudyMaterialBase, TimestampSchema, ActiveSchema):
    material_code: str
    academic_sessions_id: str
    classroom_id: str
    class_subject_id: str
    teacher_subject_id: str
    uploaded_by: str

    classroom: ClassRoomMinResponse | None = None
    uploader: UserMinResponse | None = None


class StudyMaterialUpdate(BaseSchema):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    material_type: MaterialType | None = None

    academic_sessions_id: str | None = None
    classroom_id: str | None = None
    class_subject_id: str | None = None
    teacher_subject_id: str | None = None
