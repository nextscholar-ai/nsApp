from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.model import StudyMaterial
from app.core.enums import MaterialType


class StudyMaterialService:
    """Service layer for StudyMaterial CRUD + secure file handling."""

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".png",
        ".jpg",
        ".jpeg",
        ".zip",
        ".rar",
        ".mp4",
    }

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def get_upload_root() -> str:
        return "uploads/study_materials"

    @staticmethod
    def _safe_ext(filename: str) -> str:
        _, ext = os.path.splitext(filename or "")
        return ext.lower()

    @classmethod
    def validate_extension(cls, filename: str) -> str:
        ext = cls._safe_ext(filename)
        if ext not in cls.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(cls.ALLOWED_EXTENSIONS))
            raise ValueError(f"Unsupported file extension '{ext}'. Allowed: {allowed}")
        return ext

    @classmethod
    def derive_material_type(cls, filename: str) -> MaterialType:
        ext = cls._safe_ext(filename)
        mapping = {
            ".pdf": "PDF",
            ".doc": "DOC",
            ".docx": "DOCX",
            ".ppt": "PPT",
            ".pptx": "PPTX",
            ".png": "IMAGE",
            ".jpg": "IMAGE",
            ".jpeg": "IMAGE",
            ".zip": "ARCHIVE",
            ".rar": "ARCHIVE",
            ".mp4": "VIDEO",
        }
        enum_name = mapping.get(ext)

        if enum_name and hasattr(MaterialType, enum_name):
            return getattr(MaterialType, enum_name)

        # best-effort fallback
        for fallback in ["DOCUMENT", "FILE", "PDF", "VIDEO", "IMAGE", "ARCHIVE"]:
            if hasattr(MaterialType, fallback):
                return getattr(MaterialType, fallback)

        return list(MaterialType)[0]

    def _build_storage_name(self, material_id: str, filename: str) -> str:
        ext = self.validate_extension(filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        rand = str(abs(hash((material_id, filename, timestamp))))[-8:]
        stored_name = f"{material_id}_{timestamp}_{rand}{ext}"
        return stored_name

    @staticmethod
    def _ensure_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def _save_upload(self, file: UploadFile, absolute_path: str) -> int:
        self._ensure_dir(os.path.dirname(absolute_path))
        size = 0
        with open(absolute_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            buffer.flush()
            size = os.path.getsize(absolute_path)
        return size

    @staticmethod
    def _safe_delete_file(path: Optional[str]) -> None:
        if not path:
            return
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    # ---------------------------
    # DB operations
    # ---------------------------

    def get_by_id(self, material_db_id: int) -> Optional[StudyMaterial]:
        return (
            self.db.query(StudyMaterial)
            .filter(StudyMaterial.id == material_db_id, StudyMaterial.is_active == True)  # noqa: E712
            .first()
        )

    def list_all(self) -> List[StudyMaterial]:
        return (
            self.db.query(StudyMaterial)
            .filter(StudyMaterial.is_active == True)  # noqa: E712
            .order_by(StudyMaterial.created_at.desc())
            .all()
        )

    def list_by_class_subject(self, class_subject_id: int) -> List[StudyMaterial]:
        return (
            self.db.query(StudyMaterial)
            .filter(
                StudyMaterial.class_subject_id == class_subject_id,
                StudyMaterial.is_active == True,  # noqa: E712
            )
            .order_by(StudyMaterial.created_at.desc())
            .all()
        )

    def create_material(
        self,
        *,
        title: str,
        description: Optional[str],
        academic_sessions_id: int,
        classroom_id: int,
        class_subject_id: int,
        teacher_subject_id: int,
        uploaded_by: int,
        file: UploadFile,
        material_type: Optional[str] = None,
    ) -> StudyMaterial:
        if file is None:
            raise ValueError("file is required")

        ext = self.validate_extension(file.filename)
        mt = self.derive_material_type(file.filename)
        if material_type:
            try:
                mt = MaterialType[material_type]
            except Exception:
                pass

        material = StudyMaterial(
            title=title,
            description=description,
            academic_sessions_id=academic_sessions_id,
            classroom_id=classroom_id,
            class_subject_id=class_subject_id,
            teacher_subject_id=teacher_subject_id,
            material_type=mt,
            file_name=file.filename,
            file_url="",
            file_size=0,
            mime_type=file.content_type,
            uploaded_by=uploaded_by,
        )

        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)

        stored_name = self._build_storage_name(material.material_id, file.filename)
        abs_path = os.path.join(self.get_upload_root(), stored_name)

        size = self._save_upload(file, abs_path)

        material.file_name = file.filename
        material.file_url = f"/uploads/study_materials/{stored_name}"
        material.file_size = size
        material.mime_type = file.content_type

        self.db.commit()
        self.db.refresh(material)
        return material

    def update_material(
        self,
        material_id: int,
        *,
        title: Optional[str],
        description: Optional[str],
        academic_sessions_id: Optional[int],
        classroom_id: Optional[int],
        class_subject_id: Optional[int],
        teacher_subject_id: Optional[int],
        file: Optional[UploadFile],
        material_type: Optional[str],
        updated_by: Optional[int],
    ) -> StudyMaterial:
        material = self.get_by_id(material_id)
        if not material:
            raise ValueError("Study material not found")

        if title is not None:
            material.title = title
        if description is not None:
            material.description = description
        if academic_sessions_id is not None:
            material.academic_sessions_id = academic_sessions_id
        if classroom_id is not None:
            material.classroom_id = classroom_id
        if class_subject_id is not None:
            material.class_subject_id = class_subject_id
        if teacher_subject_id is not None:
            material.teacher_subject_id = teacher_subject_id

        old_abs_path = None
        if material.file_url and material.file_url.startswith("/uploads/"):
            old_abs_path = material.file_url.replace("/uploads/", "uploads/", 1)

        if file is not None:
            mt = self.derive_material_type(file.filename)
            if material_type:
                try:
                    mt = MaterialType[material_type]
                except Exception:
                    pass

            material.material_type = mt
            stored_name = self._build_storage_name(material.material_id, file.filename)
            abs_path = os.path.join(self.get_upload_root(), stored_name)
            size = self._save_upload(file, abs_path)

            material.file_name = file.filename
            material.file_url = f"/uploads/study_materials/{stored_name}"
            material.file_size = size
            material.mime_type = file.content_type

            self._safe_delete_file(old_abs_path)

        if updated_by is not None:
            material.updated_by = updated_by

        self.db.commit()
        self.db.refresh(material)
        return material

    def delete_material(self, material_id: int) -> None:
        material = self.get_by_id(material_id)
        if not material:
            raise ValueError("Study material not found")

        abs_path = None
        if material.file_url and material.file_url.startswith("/uploads/"):
            abs_path = material.file_url.replace("/uploads/", "uploads/", 1)

        material.is_active = False
        # best-effort
        if hasattr(material, "deleted_by"):
            material.deleted_by = material.uploaded_by

        self.db.commit()
        self._safe_delete_file(abs_path)

    def increment_download(self, material_id: int) -> None:
        material = self.get_by_id(material_id)
        if not material:
            raise ValueError("Study material not found")
        material.download_count = (material.download_count or 0) + 1
        self.db.commit()

