# from pyexpat.errors import messages

# from fastapi import APIRouter
# from fastapi import Depends
# from fastapi import HTTPException

# from sqlalchemy.orm import Session

# import os
# import uuid
# from pathlib import Path

# from fastapi import (
#     UploadFile,
#     File,
#     Form,
#     HTTPException
# )

# from app.model import (
#     StudentProfile,
#     ChatMessage,

# )

# from app.schemas import (
#     ChatMessageCreate,
#     ChatMessageResponse,

# )

# from app.dependencies import (
#     get_db,
#     get_current_student
# )

# router = APIRouter(
#     prefix="/chat",
#     tags=["Chat"]
# )


# # =====================================================
# # SEND TEXT MESSAGE
# # =====================================================

# @router.post(
#     "/message/{student_id}",
#     response_model=ChatMessageResponse
# )
# def send_message(

#     student_id: str,

#     data: ChatMessageCreate,

#     db: Session = Depends(get_db)

# ):

#     student = (

#         db.query(StudentProfile)

#         .filter(
#             StudentProfile.student_id
#             == student_id
#         )

#         .first()
#     )

#     if not student:

#         raise HTTPException(
#             status_code=404,
#             detail="Student not found"
#         )

#     chat = ChatMessage(

#         student_id=student.student_id,

#         sender_type=data.sender_type,

#         sender_name=data.sender_name,

#         message=data.message
#     )

#     db.add(chat)

#     db.commit()

#     db.refresh(chat)

#     return chat


# # =====================================================
# # CHAT HISTORY
# # =====================================================

# @router.get(
#     "/messages",
#     response_model=list[ChatMessageResponse]
# )
# def my_messages(

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     return (

#         db.query(ChatMessage)

#         .filter(
#             ChatMessage.student_id
#             == student.student_id
#         )

#         .order_by(
#             ChatMessage.created_at.asc()
#         )

#         .all()
#     )


# ============================================================
# routers/chat_routers.py - Chat Routes
# ============================================================

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_user, require_role
from app.model import (
    ChatMessage,
    ChatRoom,
    StudentClass,
    StudentProfile,
    TeacherProfile,
    TeacherSubject,
    User,
)
from app.schemas import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatRoomCreate,
    ChatRoomResponse,
    ChatRoomUpdate,
    ChatUnreadCountResponse,
)

router = APIRouter(prefix="/chat", tags=["Chat"])

# ============================================================
# CHAT ROOM CRUD
# ============================================================


@router.post("/rooms", response_model=ChatRoomResponse)
async def create_chat_room(
    room_data: ChatRoomCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a chat room between teacher and student."""
    # Verify teacher is assigned to this class
    teacher = (
        db.query(TeacherProfile)
        .filter(TeacherProfile.user_id == current_user.id)
        .first()
    )

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    teacher_subject = (
        db.query(TeacherSubject)
        .filter(
            TeacherSubject.id == room_data.teacher_subject_id,
            TeacherSubject.teacher_id == teacher.teacher_id,
        )
        .first()
    )

    if not teacher_subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class",
        )

    # Check if room exists
    existing = (
        db.query(ChatRoom)
        .filter(
            ChatRoom.student_class_id == room_data.student_class_id,
            ChatRoom.teacher_subject_id == room_data.teacher_subject_id,
        )
        .first()
    )

    if existing:
        return ChatRoomResponse.model_validate(existing)

    new_room = ChatRoom(
        chat_room_id=room_data.chat_room_id,
        academic_sessions_id=room_data.academic_sessions_id,
        student_class_id=room_data.student_class_id,
        teacher_subject_id=room_data.teacher_subject_id,
        last_message=room_data.last_message,
        last_message_at=room_data.last_message_at,
        student_unread=room_data.student_unread,
        teacher_unread=room_data.teacher_unread,
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return ChatRoomResponse.model_validate(new_room)


@router.get("/rooms", response_model=list[ChatRoomResponse])
async def get_chat_rooms(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get chat rooms for current user."""
    if current_user.role == UserRole.TEACHER:
        teacher = (
            db.query(TeacherProfile)
            .filter(TeacherProfile.user_id == current_user.id)
            .first()
        )
        if teacher:
            rooms = (
                db.query(ChatRoom)
                .filter(
                    ChatRoom.teacher_subject_id.in_(
                        db.query(TeacherSubject.id).filter(
                            TeacherSubject.teacher_id == teacher.teacher_id,
                        ),
                    ),
                )
                .all()
            )
    elif current_user.role == UserRole.STUDENT:
        student = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == current_user.id)
            .first()
        )
        if student:
            student_class = (
                db.query(StudentClass)
                .filter(StudentClass.student_id == student.student_id)
                .first()
            )
            if student_class:
                rooms = (
                    db.query(ChatRoom)
                    .filter(ChatRoom.student_class_id == student_class.id)
                    .all()
                )
            else:
                rooms = []
        else:
            rooms = []
    else:
        rooms = db.query(ChatRoom).all()

    return [ChatRoomResponse.model_validate(r) for r in rooms]


@router.get("/rooms/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    room_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get chat room by ID."""
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )
    return ChatRoomResponse.model_validate(room)


@router.put("/rooms/{room_id}", response_model=ChatRoomResponse)
async def update_chat_room(
    room_id: int,
    room_data: ChatRoomUpdate,
    current_user: Annotated[
        User, Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Update a chat room."""
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )
    for key, value in room_data.model_dump(exclude_unset=True).items():
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    return ChatRoomResponse.model_validate(room)


@router.delete("/rooms/{room_id}")
async def delete_chat_room(
    room_id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a chat room and all its messages."""
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )
    db.query(ChatMessage).filter(ChatMessage.chat_room_id == room_id).delete()
    db.delete(room)
    db.commit()
    return {"success": True, "message": "Chat room deleted"}


# ============================================================
# CHAT MESSAGES
# ============================================================


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    room_id: int,
    message_data: ChatMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Send a message in a chat room."""
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )

    # Create message
    new_message = ChatMessage(
        chat_room_id=room_id,
        sender_id=current_user.id,
        message=message_data.message,
        is_edited=False,
    )

    db.add(new_message)

    # Update room
    room.last_message = message_data.message[:500]  # Truncate
    room.last_message_at = datetime.now(UTC)

    # Update unread counts
    if current_user.role == UserRole.TEACHER:
        room.student_unread += 1
    elif current_user.role == UserRole.STUDENT:
        room.teacher_unread += 1

    db.commit()
    db.refresh(new_message)

    return ChatMessageResponse.model_validate(new_message)


@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    room_id: int,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages in a chat room."""
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )

    query = db.query(ChatMessage).filter(ChatMessage.chat_room_id == room_id)

    if before:
        query = query.filter(ChatMessage.created_at < before)

    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    messages.reverse()  # Return in chronological order

    # Mark messages as read
    if current_user.role == UserRole.TEACHER:
        room.student_unread = 0
    elif current_user.role == UserRole.STUDENT:
        room.teacher_unread = 0

    db.commit()

    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.delete("/rooms/{room_id}/messages/{message_id}")
async def delete_message(
    room_id: int,
    message_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a specific message."""
    message = (
        db.query(ChatMessage)
        .filter(ChatMessage.id == message_id, ChatMessage.chat_room_id == room_id)
        .first()
    )
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    if message.sender_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages",
        )
    db.delete(message)
    db.commit()
    return {"success": True, "message": "Message deleted"}


# ============================================================
# UNREAD COUNTS
# ============================================================


@router.get("/unread", response_model=ChatUnreadCountResponse)
async def get_unread_counts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get unread message counts."""
    if current_user.role == UserRole.TEACHER:
        teacher = (
            db.query(TeacherProfile)
            .filter(TeacherProfile.user_id == current_user.id)
            .first()
        )
        if teacher:
            rooms = (
                db.query(ChatRoom)
                .filter(
                    ChatRoom.teacher_subject_id.in_(
                        db.query(TeacherSubject.id).filter(
                            TeacherSubject.teacher_id == teacher.teacher_id,
                        ),
                    ),
                )
                .all()
            )
            total_unread = sum(r.student_unread for r in rooms)
            room_counts = [
                {
                    "room_id": r.id,
                    "unread": r.student_unread,
                    "student_class": r.student_class_id,
                }
                for r in rooms
            ]
        else:
            total_unread = 0
            room_counts = []
    elif current_user.role == UserRole.STUDENT:
        student = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == current_user.id)
            .first()
        )
        if student:
            student_class = (
                db.query(StudentClass)
                .filter(StudentClass.student_id == student.student_id)
                .first()
            )
            if student_class:
                rooms = (
                    db.query(ChatRoom)
                    .filter(ChatRoom.student_class_id == student_class.id)
                    .all()
                )
                total_unread = sum(r.teacher_unread for r in rooms)
                room_counts = [
                    {
                        "room_id": r.id,
                        "unread": r.teacher_unread,
                        "teacher": r.teacher_subject_id,
                    }
                    for r in rooms
                ]
            else:
                total_unread = 0
                room_counts = []
        else:
            total_unread = 0
            room_counts = []
    else:
        total_unread = 0
        room_counts = []

    return {"total_unread": total_unread, "rooms": room_counts}
