# ============================================================
# schemas/notice.py - Production Ready & Aligned with models.py
# ============================================================

from __future__ import annotations

from typing import Optional
from datetime import date

from pydantic import Field

from app.core.enums import NoticeAudience, NoticeType
from .common import (
    BaseSchema,
    TimestampSchema,
    ActiveSchema,
    ClassRoomMinResponse,
)


class NoticeBase(BaseSchema):
    notice_id: str = Field(..., max_length=30)
    title: str = Field(..., max_length=250)
    description: str
    notice_type: NoticeType = NoticeType.GENERAL
    audience: NoticeAudience = NoticeAudience.ALL
    publish_date: date
    expiry_date: Optional[date] = None
    attachment_name: Optional[str] = Field(None, max_length=255)
    attachment_path: Optional[str] = Field(None, max_length=500)
    attachment_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    is_pinned: bool = False


class NoticeCreateForm(BaseSchema):
    academic_sessions_id: int
    classroom_id: Optional[int] = None
    title: str = Field(..., max_length=250)
    description: str
    notice_type: NoticeType = NoticeType.GENERAL
    audience: NoticeAudience = NoticeAudience.ALL
    publish_date: date
    expiry_date: Optional[date] = None
    is_pinned: bool = False


class NoticeCreate(NoticeCreateForm):
    created_by: int


class NoticeCreateMultipart(NoticeCreateForm):
    """Multipart input schema for uploading notice file(s)."""


class NoticeUpdateForm(BaseSchema):
    title: Optional[str] = Field(None, max_length=250)
    description: Optional[str] = None
    notice_type: Optional[NoticeType] = None
    audience: Optional[NoticeAudience] = None
    publish_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_pinned: Optional[bool] = None
    classroom_id: Optional[int] = None


class NoticeUpdate(NoticeUpdateForm):
    attachment_name: Optional[str] = Field(None, max_length=255)
    attachment_path: Optional[str] = Field(None, max_length=500)
    attachment_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class NoticeResponse(NoticeBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    classroom_id: Optional[int] = None
    created_by: int
    updated_by: Optional[int] = None
    deleted_by: Optional[int] = None

    classroom: Optional[ClassRoomMinResponse] = None


class NoticeFilterRequest(BaseSchema):
    notice_type: Optional[NoticeType] = None
    audience: Optional[NoticeAudience] = None
    classroom_id: Optional[int] = None
    is_pinned: Optional[bool] = None
    academic_sessions_id: Optional[int] = None

