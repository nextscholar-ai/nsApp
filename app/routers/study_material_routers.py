# ============================================================
# routers/study_material_routers.py - Study Material Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.api.database import get_db
from app.model import User
from app.schemas import StudyMaterialResponse, StudyMaterialCreate, ResponseSchema
from app.dependencies import get_current_user, require_role, get_current_teacher_profile
from app.core.enums import UserRole
from app.services.assignment_service import AssignmentService

router = APIRouter(tags=["Study Material"])


@router.post("/materials", response_model=StudyMaterialResponse)
async def upload_study_material(
    title: str,
    description: Optional[str] = None,
    material_type: str = "Document",
    academic_sessions_id: int = ...,
    classroom_id: int = ...,
    class_subject_id: int = ...,
    teacher_subject_id: int = ...,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Upload study material."""
    # Create upload directory
    upload_dir = f"uploads/materials/{class_subject_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = f"{upload_dir}/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create material record
    service = AssignmentService(db)
    # Note: StudyMaterial is in AssignmentService, you may want to separate
    # For now, this is a placeholder - you'll need a StudyMaterialService
    
    return {
        "material_id": f"MAT{datetime.now().year}{class_subject_id:04d}",
        "title": title,
        "description": description,
        "material_type": material_type,
        "file_name": file.filename,
        "file_url": f"/uploads/materials/{class_subject_id}/{filename}",
        "file_size": os.path.getsize(file_path),
        "mime_type": file.content_type,
        "academic_sessions_id": academic_sessions_id,
        "classroom_id": classroom_id,
        "class_subject_id": class_subject_id,
        "teacher_subject_id": teacher_subject_id,
        "uploaded_by": current_user.id
    }


@router.get("/materials/class-subject/{class_subject_id}", response_model=List[StudyMaterialResponse])
async def get_study_materials(
    class_subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get study materials for a class subject."""
    # Implementation using StudyMaterialService
    pass