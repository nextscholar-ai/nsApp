# ============================================================
# schemas/notice.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import date

from pydantic import Field

from app.core.enums import NoticeAudience, NoticeType

from .common import (
    ActiveSchema,
    BaseSchema,
    ClassRoomMinResponse,
    TimestampSchema,
)


class NoticeBase(BaseSchema):
    title: str = Field(..., max_length=250)
    description: str
    notice_type: NoticeType = NoticeType.GENERAL
    audience: NoticeAudience = NoticeAudience.ALL
    publish_date: date
    expiry_date: date | None = None
    attachment_name: str | None = Field(None, max_length=255)
    attachment_path: str | None = Field(None, max_length=500)
    attachment_size: int | None = None
    mime_type: str | None = Field(None, max_length=100)
    is_pinned: bool = False


class NoticeCreateForm(BaseSchema):
    academic_sessions_id: str
    classroom_id: str | None = None
    title: str = Field(..., max_length=250)
    description: str
    notice_type: NoticeType = NoticeType.GENERAL
    audience: NoticeAudience = NoticeAudience.ALL
    publish_date: date
    expiry_date: date | None = None
    is_pinned: bool = False


class NoticeCreate(NoticeCreateForm):
    created_by: str


class NoticeCreateMultipart(NoticeCreateForm):
    """Multipart input schema for uploading notice file(s)."""


class NoticeUpdateForm(BaseSchema):
    title: str | None = Field(None, max_length=250)
    description: str | None = None
    notice_type: NoticeType | None = None
    audience: NoticeAudience | None = None
    publish_date: date | None = None
    expiry_date: date | None = None
    is_pinned: bool | None = None
    classroom_id: str | None = None


class NoticeUpdate(NoticeUpdateForm):
    attachment_name: str | None = Field(None, max_length=255)
    attachment_path: str | None = Field(None, max_length=500)
    attachment_size: int | None = None
    mime_type: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class NoticeResponse(NoticeBase, TimestampSchema, ActiveSchema):
    notice_code: str
    academic_sessions_id: str
    classroom_id: str | None = None
    created_by: str
    updated_by: str | None = None
    deleted_by: str | None = None

    classroom: ClassRoomMinResponse | None = None


class NoticeFilterRequest(BaseSchema):
    notice_type: NoticeType | None = None
    audience: NoticeAudience | None = None
    classroom_id: str | None = None
    is_pinned: bool | None = None
    academic_sessions_id: str | None = None
