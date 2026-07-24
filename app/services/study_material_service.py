from __future__ import annotations

import contextlib
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from app.core.enums import MaterialType
from app.model import StudyMaterial

if TYPE_CHECKING:
    from fastapi import UploadFile
    from sqlalchemy.orm import Session


class StudyMaterialService:
    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {
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

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def get_upload_root() -> str:
        return "uploads/study_materials"

    @staticmethod
    def _safe_ext(filename: str) -> str:
        ext = Path(filename or "").suffix
        return ext.lower()

    @classmethod
    def validate_extension(cls, filename: str) -> str:
        ext = cls._safe_ext(filename)
        if ext not in cls.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(cls.ALLOWED_EXTENSIONS))
            msg = f"Unsupported file extension '{ext}'. Allowed: {allowed}"
            raise ValueError(msg)
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

        return next(iter(MaterialType))

    def _build_storage_name(self, material_id: str, filename: str) -> str:
        ext = self.validate_extension(filename)
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        rand = str(abs(hash((material_id, filename, timestamp))))[-8:]
        return f"{material_id}_{timestamp}_{rand}{ext}"

    @staticmethod
    def _ensure_dir(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def _save_upload(self, file: UploadFile, absolute_path: str) -> int:
        self._ensure_dir(str(Path(absolute_path).parent))
        with Path(absolute_path).open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            buffer.flush()
            return Path(absolute_path).stat().st_size

    @staticmethod
    def _safe_delete_file(path: str | None) -> None:
        if not path:
            return
        try:
            p = Path(path)
            if p.exists():
                p.unlink()
        except Exception:  # noqa: S110
            pass

    # ---------------------------
    # DB operations
    # ---------------------------

    def get_by_id(self, material_db_id: str) -> StudyMaterial | None:
        return (
            self.db.query(StudyMaterial)
            .filter(
                StudyMaterial.material_code == material_db_id,
                StudyMaterial.is_active.is_(True),
            )
            .first()
        )

    def list_all(self) -> list[StudyMaterial]:
        return (
            self.db.query(StudyMaterial)
            .filter(StudyMaterial.is_active.is_(True))
            .order_by(StudyMaterial.created_at.desc())
            .all()
        )

    def list_by_class_subject(self, class_subject_id: str) -> list[StudyMaterial]:
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
        description: str | None,
        academic_sessions_id: str,
        classroom_id: str,
        class_subject_id: str,
        teacher_subject_id: str,
        uploaded_by: str,
        file: UploadFile,
        material_type: str | None = None,
    ) -> StudyMaterial:
        if file is None:
            msg = "file is required"
            raise ValueError(msg)

        self.validate_extension(file.filename)
        mt = self.derive_material_type(file.filename)
        if material_type:
            with contextlib.suppress(Exception):
                mt = MaterialType[material_type]

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

        stored_name = self._build_storage_name(material.material_code, file.filename)
        abs_path = str(Path(self.get_upload_root()) / stored_name)

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
        material_id: str,
        *,
        title: str | None,
        description: str | None,
        academic_sessions_id: str | None,
        classroom_id: str | None,
        class_subject_id: str | None,
        teacher_subject_id: str | None,
        file: UploadFile | None,
        material_type: str | None,
        updated_by: str | None,
    ) -> StudyMaterial:
        material = self.get_by_id(material_id)
        if not material:
            msg = "Study material not found"
            raise ValueError(msg)

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
                with contextlib.suppress(Exception):
                    mt = MaterialType[material_type]

            material.material_type = mt
            stored_name = self._build_storage_name(material.material_code, file.filename)
            abs_path = str(Path(self.get_upload_root()) / stored_name)
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

    def delete_material(self, material_id: str) -> None:
        material = self.get_by_id(material_id)
        if not material:
            msg = "Study material not found"
            raise ValueError(msg)

        abs_path = None
        if material.file_url and material.file_url.startswith("/uploads/"):
            abs_path = material.file_url.replace("/uploads/", "uploads/", 1)

        material.is_active = False
        # best-effort
        if hasattr(material, "deleted_by"):
            material.deleted_by = material.uploaded_by

        self.db.commit()
        self._safe_delete_file(abs_path)

    def increment_download(self, material_id: str) -> None:
        material = self.get_by_id(material_id)
        if not material:
            msg = "Study material not found"
            raise ValueError(msg)
        material.download_count = (material.download_count or 0) + 1
        self.db.commit()
