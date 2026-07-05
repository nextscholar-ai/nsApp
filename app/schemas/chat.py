# ============================================================
# schemas.py - Production Ready & Aligned with models.py
# ============================================================

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional, Generic, TypeVar, List, Dict, Any, Union
from datetime import datetime, date, time
from decimal import Decimal
from  enum import Enum

from app.core.enums import (
    UserRole, 
    AssignmentStatus, 
    ExamStatus, 
    FeeStatus,
    NoticeType,
    NoticeAudience,
    MaterialType,
    AttendanceStatus,
    LectureStatus,
    PromotionType,
    Gender
)

# ============================================================
# TYPE VARIABLES & BASE SCHEMAS
# ============================================================

T = TypeVar('T')


from .common import *
from .teacher_student_links import StudentClassResponse


# ============================================================
# ChatRoomBase
# ============================================================

class ChatRoomBase(BaseSchema):
    chat_room_id: str = Field(..., max_length=30)
    last_message: Optional[str] = Field(None, max_length=500)
    last_message_at: Optional[datetime] = None
    student_unread: int = 0
    teacher_unread: int = 0


# ============================================================
# ChatRoomCreate
# ============================================================

class ChatRoomCreate(ChatRoomBase):
    academic_sessions_id: int
    student_class_id: int
    teacher_subject_id: int


# ============================================================
# ChatRoomResponse
# ============================================================

class ChatRoomResponse(ChatRoomBase, TimestampSchema, ActiveSchema):
    id: int
    academic_sessions_id: int
    student_class_id: int
    teacher_subject_id: int
    
    student_class: Optional[StudentClassResponse] = None


# ============================================================
# ChatMessageBase
# ============================================================

class ChatMessageBase(BaseSchema):
    message: str
    is_edited: bool = False
    edited_at: Optional[datetime] = None


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
    id: int
    chat_room_id: int
    sender_id: int
    
    sender: Optional[UserMinResponse] = None



# ============================================================
# ChatRoomUpdate
# ============================================================

class ChatRoomUpdate(BaseSchema):
    last_message: Optional[str] = Field(None, max_length=500)
    last_message_at: Optional[datetime] = None
    student_unread: Optional[int] = None
    teacher_unread: Optional[int] = None
    is_active: Optional[bool] = None


# ============================================================
# ChatConversationResponse
# ============================================================

class ChatConversationResponse(BaseSchema):
    chat_room: ChatRoomResponse
    messages: List[ChatMessageResponse] = []


# ============================================================
# ChatUnreadCountResponse
# ============================================================

class ChatUnreadCountResponse(BaseSchema):
    total_unread: int = 0
