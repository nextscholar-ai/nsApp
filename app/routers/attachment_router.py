# ============================================================
# routers/attachment_router.py - Generic Attachment Endpoints
# ============================================================
#
# A polymorphic attachment store usable by any entity (assignments,
# study material, exams, chat, etc.) via entity_type + entity_id.

import base64
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_user
from app.model import Attachment, User

router = APIRouter(prefix="/attachments", tags=["Attachments"])


ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "image/jpeg",
    "image/png",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _normalize_mime_type(mime_type: str) -> str:
    mime_type_norm = mime_type.strip().lower()
    if mime_type_norm in ("application/jpg", "image/jpg"):
        mime_type_norm = "image/jpeg"
    if mime_type_norm == "application/txt":
        mime_type_norm = "text/plain"
    return mime_type_norm


def _decode_base64_to_bytes(data: str) -> bytes:
    try:
        # Accept raw base64 or data URL format: data:<mime>;base64,<...>
        if data.strip().startswith("data:") and "," in data:
            data = data.split(",", 1)[1]
        return base64.b64decode(data, validate=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 file data",
        ) from e


def _generate_attachment_code() -> str:
    return f"ATC-{secrets.token_hex(8).upper()}"[:30]


@router.post("/upload")
async def upload_attachment(
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Upload a file (base64-encoded) and associate it with any entity via
    entity_type/entity_id, e.g. {"entity_type": "assignment", "entity_id": 12}.
    """
    entity_type: str | None = payload.get("entity_type")
    entity_id: str | None = payload.get("entity_id")
    file_name: str | None = payload.get("file_name")
    mime_type: str | None = payload.get("mime_type")
    file_data_b64: str | None = payload.get("file_data")

    if not entity_type or entity_id is None:
        raise HTTPException(
            status_code=400,
            detail="entity_type and entity_id are required",
        )
    if not file_name or not mime_type or not file_data_b64:
        raise HTTPException(
            status_code=400,
            detail="file_name, mime_type, file_data are required",
        )

    mime_type_norm = _normalize_mime_type(mime_type)
    if mime_type_norm not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    raw = _decode_base64_to_bytes(file_data_b64)

    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(raw) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File exceeds maximum allowed size (10 MB)",
        )

    # Always generate the code server-side to guarantee uniqueness.
    attachment_code = _generate_attachment_code()

    attachment = Attachment(
        attachment_code=attachment_code,
        entity_type=entity_type.lower(),
        entity_id=entity_id,
        file_name=file_name,
        mime_type=mime_type_norm,
        file_size=len(raw),
        file_data=raw,
        created_by=current_user.id,
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return {
        "success": True,
        "attachment_id": attachment.attachment_code,
        "attachment_code": attachment.attachment_code,
        "file_name": attachment.file_name,
        "file_size": attachment.file_size,
    }


@router.get("/{attachment_id}")
async def download_attachment(
    attachment_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    attachment = (
        db.query(Attachment)
        .filter(Attachment.attachment_code == attachment_id, Attachment.is_active)
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    headers = {"Content-Disposition": f'inline; filename="{attachment.file_name}"'}
    return Response(
        content=attachment.file_data,
        media_type=attachment.mime_type,
        headers=headers,
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def list_entity_attachments(
    entity_type: str,
    entity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    attachments = (
        db.query(Attachment)
        .filter(
            Attachment.entity_type == entity_type.lower(),
            Attachment.entity_id == entity_id,
            Attachment.is_active,
        )
        .order_by(Attachment.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "data": [
            {
                "id": a.attachment_code,
                "attachment_code": a.attachment_code,
                "file_name": a.file_name,
                "mime_type": a.mime_type,
                "file_size": a.file_size,
                "created_at": a.created_at,
            }
            for a in attachments
        ],
    }


@router.put("/{attachment_id}")
async def update_attachment(
    attachment_id: str,
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update attachment metadata (file_name, mime_type)."""
    attachment = (
        db.query(Attachment).filter(Attachment.attachment_code == attachment_id).first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    is_owner = attachment.created_by == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.ADMIN.value)
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update this attachment",
        )

    file_name = payload.get("file_name")
    mime_type = payload.get("mime_type")
    if file_name is not None:
        attachment.file_name = file_name
    if mime_type is not None:
        mime_type_norm = _normalize_mime_type(mime_type)
        if mime_type_norm not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        attachment.mime_type = mime_type_norm

    db.commit()
    db.refresh(attachment)

    return {
        "success": True,
        "attachment_id": attachment.attachment_code,
        "file_name": attachment.file_name,
        "mime_type": attachment.mime_type,
    }


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Soft-delete an attachment (uploader or admin only)."""
    attachment = (
        db.query(Attachment).filter(Attachment.attachment_code == attachment_id).first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    is_owner = attachment.created_by == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.ADMIN.value)
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this attachment",
        )

    attachment.is_active = False
    db.commit()

    return {"success": True, "message": "Attachment deleted"}
