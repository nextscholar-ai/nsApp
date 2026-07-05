import uuid
import secrets

from sqlalchemy import Enum

from datetime import datetime
from app.core.constants import *
from app.core.enums import *
from app.core.mixins import *
from app.helpers.code_generators import *
from app.helpers.validators import Validators
from app.helpers.date_utils import DateUtils
from app.helpers.security import SecurityUtils


from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    Time,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    Numeric

)

from sqlalchemy.orm import (
    relationship,
    declared_attr
)

from app.api.database import Base


# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# CHATROOM TABLE
# ============================================================

class ChatRoom(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "chat_rooms"

    id = Column(
        Integer,
        primary_key=True
    )

    chat_room_id = Column(

        String(30),

        unique=True,

        nullable=False,

        default=generate_chat_room_id,

        index=True

    )

    academic_sessions_id = Column(

        Integer,

        ForeignKey("academic_sessions.id"),

        nullable=False,

        index=True

    )

    student_class_id = Column(

        Integer,

        ForeignKey("student_classes.id"),

        nullable=False,

        index=True

    )

    teacher_subject_id = Column(

        Integer,

        ForeignKey("teacher_subjects.id"),

        nullable=False,

        index=True

    )

    last_message = Column(

        String(500)

    )

    last_message_at = Column(

        DateTime

    )

    student_unread = Column(

        Integer,

        default=0,

        nullable=False

    )

    teacher_unread = Column(

        Integer,

        default=0,

        nullable=False

    )

    academic_sessions = relationship(
        "AcademicSession"
    )

    student_class = relationship(
        "StudentClass"
    )

    teacher_subject = relationship(
        "TeacherSubject"
    )

    messages = relationship(

        "ChatMessage",

        back_populates="chat_room",

        cascade="all, delete-orphan"

    )

    __table_args__ = (

        UniqueConstraint(

            "student_class_id",

            "teacher_subject_id",

            name="uq_chat_room"

        ),

        Index(

            "idx_chat_room",

            "teacher_subject_id",

            "student_class_id"

        ),

    )


# ============================================================
# CHATMESSAGE TABLE
# ============================================================

class ChatMessage(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True
    )

    chat_room_id = Column(

        Integer,

        ForeignKey("chat_rooms.id"),

        nullable=False,

        index=True

    )

    sender_id = Column(

        Integer,

        ForeignKey("users.id"),

        nullable=False,

        index=True

    )

    message = Column(

        Text,

        nullable=False

    )

    is_edited = Column(

        Boolean,

        default=False

    )

    edited_at = Column(

        DateTime

    )

    chat_room = relationship(

        "ChatRoom",

        back_populates="messages"

    )

    sender = relationship(

        "User"

    )

    __table_args__ = (

        Index(

            "idx_chat_message",

            "chat_room_id",

            "created_at"

        ),

    )

