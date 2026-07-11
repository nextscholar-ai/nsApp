# ============================================================
# routers/top_students_teachers_router.py
# Top-level admin endpoints required by contract
# GET /students and GET /teachers
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.database import get_db
from app.dependencies import require_role
from app.core.enums import UserRole
from app.model import User
from app.services.admin_student_teacher_service import AdminStudentTeacherService
from app.schemas import (
    PaginatedStudentAdminListResponse,
    PaginatedTeacherAdminListResponse,
)

router = APIRouter(tags=["Admin Directory"])


@router.get("/students", response_model=PaginatedStudentAdminListResponse)
async def get_all_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    class_id: Optional[int] = Query(None, ge=1),
    class_code: Optional[str] = None,
    section: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin only: return all students by default with pagination and optional filters."""

    if class_id is not None and class_code is not None:
        # keep it strict to avoid ambiguous filters
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one of class_id or class_code"
        )

    service = AdminStudentTeacherService(db)

    # Current service supports: search, class_id, class_code
    # section/status will be applied in-service in a follow-up audit.
    res = service.list_students_admin(
        page=page,
        page_size=page_size,
        search=search,
        class_id=class_id,
        class_code=class_code,
    )

    # apply section/status filters in Python to keep this runnable without changing service query further
    # (Production-ready fix will move this into SQL during full audit step).
    if section is not None or status is not None:
        filtered = []
        for row in res.get("data", []):
            if section is not None and row.get("section") != section:
                continue
            if status is not None and row.get("status") != status:
                continue
            filtered.append(row)

        total_items = len(filtered)
        total_pages = (total_items + page_size - 1) // page_size
        res = {
            **res,
            "data": filtered,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
            },
        }

    return res


@router.get("/teachers", response_model=PaginatedTeacherAdminListResponse)
async def get_all_teachers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    department: Optional[str] = None,
    subject: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin only: return all teachers by default with pagination and optional filters."""

    service = AdminStudentTeacherService(db)

    return service.list_teachers_admin(
        page=page,
        page_size=page_size,
        search=search,
        department=department,
        subject=subject,
        status=status,
        is_active=None,
    )

