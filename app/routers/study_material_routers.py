# ============================================================
# routers/study_material_routers.py - Study Material Routes (File-based)
# ============================================================

from __future__ import annotations

from typing import List, Optional
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_user, require_role
from app.model import User
from app.services.study_material_service import StudyMaterialService

# Import schemas directly to avoid pulling in the whole schemas package
from app.schemas.study_material import StudyMaterialResponse
from app.schemas.common import ResponseSchema

router = APIRouter(prefix="/study-materials", tags=["Study Materials"])


@router.post("", response_model=StudyMaterialResponse)
async def create_study_material(
    title: str,
    description: Optional[str] = None,
    material_type: Optional[str] = None,
    academic_sessions_id: int = ...,
    classroom_id: int = ...,
    class_subject_id: int = ...,
    teacher_subject_id: int = ...,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin uploads actual study material files."""
    try:
        service = StudyMaterialService(db)
        material = service.create_material(
            title=title,
            description=description,
            material_type=material_type,
            academic_sessions_id=academic_sessions_id,
            classroom_id=classroom_id,
            class_subject_id=class_subject_id,
            teacher_subject_id=teacher_subject_id,
            uploaded_by=current_user.id,
            file=file,
        )
        return StudyMaterialResponse.model_validate(material)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[StudyMaterialResponse])
async def list_study_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get study materials."""
    service = StudyMaterialService(db)
    materials = service.list_all()
    return [StudyMaterialResponse.model_validate(m) for m in materials]


@router.get("/class-subject/{class_subject_id}", response_model=List[StudyMaterialResponse])
async def get_materials_for_class_subject(
    class_subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get study materials for a specific class-subject mapping."""
    service = StudyMaterialService(db)
    materials = service.list_by_class_subject(class_subject_id)
    return [StudyMaterialResponse.model_validate(m) for m in materials]


@router.get("/{id}", response_model=StudyMaterialResponse)
async def get_study_material(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StudyMaterialService(db)
    material = service.get_by_id(id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study material not found")
    return StudyMaterialResponse.model_validate(material)


def _material_abs_path(file_url: str) -> Optional[str]:
    if not file_url:
        return None
    if file_url.startswith("/uploads/"):
        return file_url.replace("/uploads/", "uploads/", 1)
    if file_url.startswith("uploads/"):
        return file_url
    return None


@router.get("/{id}/view")
async def view_study_material(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Students must be able to view study materials."""
    service = StudyMaterialService(db)
    material = service.get_by_id(id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study material not found")

    if current_user.role not in [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    abs_path = _material_abs_path(material.file_url)
    if not abs_path or not os.path.exists(abs_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server")

    filename = material.file_name or os.path.basename(abs_path)

    return FileResponse(
        abs_path,
        media_type=material.mime_type or "application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get("/{id}/download")
async def download_study_material(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Students must be able to download study materials."""
    service = StudyMaterialService(db)
    material = service.get_by_id(id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study material not found")

    if current_user.role not in [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    # increment download count
    try:
        service.increment_download(id)
    except Exception:
        pass

    abs_path = _material_abs_path(material.file_url)
    if not abs_path or not os.path.exists(abs_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server")

    filename = material.file_name or os.path.basename(abs_path)

    return FileResponse(
        abs_path,
        media_type=material.mime_type or "application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.put("/{id}", response_model=StudyMaterialResponse)
async def update_study_material(
    id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    material_type: Optional[str] = None,
    academic_sessions_id: Optional[int] = None,
    classroom_id: Optional[int] = None,
    class_subject_id: Optional[int] = None,
    teacher_subject_id: Optional[int] = None,
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin updates study material metadata and optionally replaces the file."""
    service = StudyMaterialService(db)
    try:
        material = service.update_material(
            id,
            title=title,
            description=description,
            academic_sessions_id=academic_sessions_id,
            classroom_id=classroom_id,
            class_subject_id=class_subject_id,
            teacher_subject_id=teacher_subject_id,
            file=file,
            material_type=material_type,
            updated_by=current_user.id,
        )
        return StudyMaterialResponse.model_validate(material)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{id}")
async def delete_study_material(
    id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = StudyMaterialService(db)
    try:
        service.delete_material(id)
        return ResponseSchema(success=True, message="Study material deleted").model_dump()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

