# from app.dependencies import get_current_teacher
# from fastapi import (
#     APIRouter,
#     Depends,
#     UploadFile,
#     File,
#     Form,
#     HTTPException
# )

# from app.schemas import NoticeResponse

# from sqlalchemy.orm import Session

# from app.api.database import get_db

# from app.model import (
#     Notice,
#     NoticeAttachment
# )

# import os
# import shutil
# import uuid

# router = APIRouter(
#     prefix="/notices",
#     tags=["Notice Board"]
# )

# UPLOAD_DIR = "uploads/notices"

# os.makedirs(
#     UPLOAD_DIR,
#     exist_ok=True
# )


# @router.post("/", response_model=NoticeResponse)
# def create_notice(
#     title: str = Form(...),
#     description: str = Form(None),
#     files: list[UploadFile] = File([]),
#     teacher=Depends(
#         get_current_teacher
#     ),
#     db: Session = Depends(get_db)
# ):

#     notice = Notice(
#         title=title,
#         description=description
#     )

#     db.add(notice)
#     db.commit()
#     db.refresh(notice)

#     for file in files:

#         extension = os.path.splitext(
#             file.filename
#         )[1]

#         unique_name = (
#             str(uuid.uuid4()) +
#             extension
#         )

#         file_path = os.path.join(
#             UPLOAD_DIR,
#             unique_name
#         )

#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(
#                 file.file,
#                 buffer
#             )

#         file_url = f"/uploads/notices/{unique_name}"

#         attachment = NoticeAttachment(
#             notice_id=notice.id,
#             file_name=file.filename,
#             file_path=file_url,
#             file_type=file.content_type
#         )

#         db.add(attachment)

#     db.commit()


#     db.refresh(notice)

#     notice = db.query(Notice).filter(
#         Notice.notice_code == notice.id
#     ).first()

#     return notice


# @router.get("/",response_model=list[NoticeResponse])
# def get_all_notices(
#     db: Session = Depends(get_db)
# ):

#     notices = db.query(
#         Notice
#     ).order_by(
#         Notice.created_at.desc()
#     ).all()

#     return notices


# @router.get("/{notice_id}",response_model=NoticeResponse)
# def get_notice(
#     notice_id: str,
#     db: Session = Depends(get_db)
# ):

#     notice = db.query(
#         Notice
#     ).filter(
#         Notice.notice_code == notice_id
#     ).first()

#     if not notice:
#         raise HTTPException(
#             status_code=404,
#             detail="Notice not found"
#         )

#     return notice


# @router.delete("/{notice_id}")
# def delete_notice(
#     notice_id: str,
#     teacher=Depends(
#         get_current_teacher
#     ),
#     db: Session = Depends(get_db)
# ):

#     notice = db.query(
#         Notice
#     ).filter(
#         Notice.notice_code == notice_id
#     ).first()

#     if not notice:
#         raise HTTPException(
#             status_code=404,
#             detail="Notice not found"
#         )

#     for attachment in notice.attachments:

#         if os.path.exists(
#             attachment.file_path
#         ):
#             os.remove(
#                 attachment.file_path
#             )

#     db.delete(notice)

#     db.commit()

#     return {
#         "message": "Notice deleted"
#     }


# ============================================================
# routers/notice_routers.py - Notice Routes
# ============================================================

import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import NoticeAudience, NoticeType, UserRole
from app.dependencies import get_current_user, require_role
from app.model import Notice, User
from app.schemas import NoticeResponse

router = APIRouter(prefix="/notices", tags=["Notice Board"])

# ============================================================
# NOTICE CRUD
# ============================================================

UPLOAD_DIR = Path("uploads") / "notices"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _notice_file_disk_path(stored_name: str) -> Path:
    return UPLOAD_DIR / stored_name


def _delete_if_exists(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:  # noqa: S110
        # Don't crash API because of cleanup errors.
        pass


@router.post("/", response_model=NoticeResponse)
async def create_notice(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    notice_type: Annotated[NoticeType, Form()] = NoticeType.GENERAL,
    audience: Annotated[NoticeAudience, Form()] = NoticeAudience.ALL,
    publish_date: date = Form(...),
    expiry_date: Annotated[date | None, Form()] = None,
    is_pinned: Annotated[bool, Form()] = False,
    academic_sessions_id: str = Form(...),
    classroom_id: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Create a new notice, optionally with an uploaded attachment."""
    attachment_name = None
    attachment_path = None
    attachment_size = None
    mime_type = None

    # Only a real, named file upload counts as an attachment. Some HTTP
    # clients still send an empty file part even when "no file" was intended.
    if file is not None and file.filename:
        original_name = file.filename or "notice"
        ext = Path(original_name).suffix
        stored_name = f"{uuid.uuid4().hex}{ext}" if ext else uuid.uuid4().hex

        disk_path = _notice_file_disk_path(stored_name)

        # Save to disk
        with disk_path.open("wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)

        attachment_name = original_name
        attachment_path = f"/uploads/notices/{stored_name}"
        attachment_size = disk_path.stat().st_size
        mime_type = file.content_type

    new_notice = Notice(
        academic_sessions_id=academic_sessions_id,
        classroom_id=classroom_id,
        title=title,
        description=description,
        notice_type=notice_type,
        audience=audience,
        publish_date=publish_date,
        expiry_date=expiry_date,
        attachment_name=attachment_name,
        attachment_path=attachment_path,
        attachment_size=attachment_size,
        mime_type=mime_type,
        is_pinned=is_pinned,
        created_by=current_user.id,
    )

    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)

    return NoticeResponse.model_validate(new_notice)


@router.get("/", response_model=list[NoticeResponse])
async def get_notices(
    notice_type: NoticeType | None = None,
    audience: NoticeAudience | None = None,
    is_pinned: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notices with filters."""
    query = db.query(Notice).filter(
        Notice.is_active,
        Notice.publish_date <= datetime.now(UTC).date(),
    )

    if notice_type:
        query = query.filter(Notice.notice_type == notice_type)

    if is_pinned is not None:
        query = query.filter(Notice.is_pinned == is_pinned)

    # Filter by audience
    if current_user.role == UserRole.STUDENT:
        query = query.filter(
            Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.STUDENT]),
        )
    elif current_user.role == UserRole.TEACHER:
        query = query.filter(
            Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.TEACHER]),
        )
    elif current_user.role == UserRole.ADMIN:
        pass

    # Order by pinned first, then by publish date
    notices = query.order_by(Notice.is_pinned.desc(), Notice.publish_date.desc()).all()

    return [NoticeResponse.model_validate(n) for n in notices]


def _notice_access_check(notice: Notice, current_user: User) -> None:
    # Reuse your audience rules (similar to GET /notices)
    if not notice:
        return

    if notice.expiry_date is not None and datetime.now(UTC).date() > notice.expiry_date:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice expired",
        )

    if notice.publish_date > datetime.now(UTC).date():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not yet published",
        )

    if (
        current_user.role == UserRole.STUDENT
        and notice.audience not in [NoticeAudience.ALL, NoticeAudience.STUDENT]
    ) or (
        current_user.role == UserRole.TEACHER
        and notice.audience not in [NoticeAudience.ALL, NoticeAudience.TEACHER]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )


@router.get("/{notice_id}", response_model=NoticeResponse)
async def get_notice(
    notice_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get notice by ID."""
    notice = db.query(Notice).filter(Notice.notice_code == notice_id).first()

    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )

    _notice_access_check(notice, current_user)

    return NoticeResponse.model_validate(notice)


@router.put("/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: str,
    title: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    notice_type: Annotated[NoticeType | None, Form()] = None,
    audience: Annotated[NoticeAudience | None, Form()] = None,
    publish_date: Annotated[date | None, Form()] = None,
    expiry_date: Annotated[date | None, Form()] = None,
    is_pinned: Annotated[bool | None, Form()] = None,
    classroom_id: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Update notice."""
    notice = db.query(Notice).filter(Notice.notice_code == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )

    update_map = {
        "title": title,
        "description": description,
        "notice_type": notice_type,
        "audience": audience,
        "publish_date": publish_date,
        "expiry_date": expiry_date,
        "is_pinned": is_pinned,
        "classroom_id": classroom_id,
    }

    for key, value in update_map.items():
        if value is not None:
            setattr(notice, key, value)

    # Replace file if provided
    if file is not None:
        # Remove old file (best-effort)
        if notice.attachment_path:
            old_disk = Path(notice.attachment_path.replace("/uploads/", "uploads/"))
            _delete_if_exists(old_disk)

        original_name = file.filename or "notice"
        ext = Path(original_name).suffix
        stored_name = f"{uuid.uuid4().hex}{ext}" if ext else uuid.uuid4().hex
        disk_path = _notice_file_disk_path(stored_name)

        with disk_path.open("wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)

        notice.attachment_name = original_name
        notice.attachment_path = f"/uploads/notices/{stored_name}"
        notice.attachment_size = disk_path.stat().st_size
        notice.mime_type = file.content_type

    notice.updated_by = current_user.id
    db.commit()
    db.refresh(notice)

    return NoticeResponse.model_validate(notice)


@router.delete("/{notice_id}")
async def delete_notice(
    notice_id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Soft-delete notice + remove attachment file from disk (best-effort)."""
    notice = db.query(Notice).filter(Notice.notice_code == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )

    # Best-effort cleanup of old file
    if notice.attachment_path:
        stored_name = Path(notice.attachment_path).name
        _delete_if_exists(_notice_file_disk_path(stored_name))

    notice.is_active = False
    notice.deleted_by = current_user.id
    db.commit()

    return {"success": True, "message": "Notice deleted successfully"}


# ============================================================
# NOTICE PIN/UNPIN
# ============================================================


@router.post("/{notice_id}/pin")
async def pin_notice(
    notice_id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Pin a notice."""
    notice = db.query(Notice).filter(Notice.notice_code == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )

    notice.is_pinned = True
    db.commit()

    return {"success": True, "message": "Notice pinned successfully"}


@router.get("/{notice_id}/view")
async def view_notice_file(
    notice_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    notice = db.query(Notice).filter(Notice.notice_code == notice_id).first()
    if not notice or not notice.attachment_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice file not found",
        )

    _notice_access_check(notice, current_user)

    stored_name = Path(notice.attachment_path).name
    disk_path = _notice_file_disk_path(stored_name)
    if not disk_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File missing on server",
        )

    return FileResponse(
        disk_path,
        media_type=notice.mime_type,
        filename=notice.attachment_name or stored_name,
    )


@router.get("/{notice_id}/download")
async def download_notice_file(
    notice_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    notice = db.query(Notice).filter(Notice.notice_code == notice_id).first()
    if not notice or not notice.attachment_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice file not found",
        )

    _notice_access_check(notice, current_user)

    stored_name = Path(notice.attachment_path).name
    disk_path = _notice_file_disk_path(stored_name)
    if not disk_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File missing on server",
        )

    # FileResponse sets Content-Disposition to inline by default; use attachment for download.
    return FileResponse(
        disk_path,
        media_type=notice.mime_type,
        filename=notice.attachment_name or stored_name,
        headers={
            "Content-Disposition": f'attachment; filename="{notice.attachment_name or stored_name}"',
        },
    )


@router.post("/{notice_id}/unpin")
async def unpin_notice(
    notice_id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Unpin a notice."""
    notice = db.query(Notice).filter(Notice.notice_code == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )

    notice.is_pinned = False
    db.commit()

    return {"success": True, "message": "Notice unpinned successfully"}
