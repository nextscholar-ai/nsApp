# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from datetime import datetime
from typing import TypeVar

from pydantic import Field

from .common import (
    ActiveSchema,
    BaseSchema,
    TimestampSchema,
    UserMinResponse,
)
from .teacher_student_links import StudentClassResponse

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar("T")

# ============================================================
# ChatRoomBase
# ============================================================


class ChatRoomBase(BaseSchema):
    chat_room_id: str = Field(..., max_length=30)
    last_message: str | None = Field(None, max_length=500)
    last_message_at: datetime | None = None
    student_unread: int = 0
    teacher_unread: int = 0


# ============================================================
# ChatRoomCreate
# ============================================================


class ChatRoomCreate(ChatRoomBase):
    academic_sessions_id: str
    student_class_id: int
    teacher_subject_id: int


# ============================================================
# ChatRoomResponse
# ============================================================


class ChatRoomResponse(ChatRoomBase, TimestampSchema, ActiveSchema):
    chat_room_code: str
    academic_sessions_id: str
    student_class_id: str
    teacher_subject_id: str

    student_class: StudentClassResponse | None = None


# ============================================================
# ChatMessageBase
# ============================================================


class ChatMessageBase(BaseSchema):
    message: str
    is_edited: bool = False
    edited_at: datetime | None = None


# ============================================================
# ChatMessageCreate
# ============================================================


class ChatMessageCreate(ChatMessageBase):
    chat_room_id: int
    sender_id: int


# ============================================================
# ChatMessageResponse
# ============================================================


class ChatMessageResponse(ChatMessageBase, TimestampSchema, ActiveSchema):
    chat_message_code: str
    chat_room_id: str
    sender_id: str

    sender: UserMinResponse | None = None


# ============================================================
# ChatRoomUpdate
# ============================================================


class ChatRoomUpdate(BaseSchema):
    last_message: str | None = Field(None, max_length=500)
    last_message_at: datetime | None = None
    student_unread: int | None = None
    teacher_unread: int | None = None
    is_active: bool | None = None


# ============================================================
# ChatConversationResponse
# ============================================================


class ChatConversationResponse(BaseSchema):
    chat_room: ChatRoomResponse
    messages: list[ChatMessageResponse] = Field(default_factory=list)


# ============================================================
# ChatUnreadCountResponse
# ============================================================


class ChatUnreadCountResponse(BaseSchema):
    total_unread: int = 0
