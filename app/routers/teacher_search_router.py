# ============================================================
# app/routers/teacher_search_router.py
# ============================================================
#
# Natural-language search endpoint for teachers, mirroring
# student_search_router.py. ADDITIVE: existing ID-based teacher
# endpoints (teacher_router.py) are untouched.
#
# Access: Admin only (staff-directory lookup).

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.core.exceptions import SearchValidationError
from app.dependencies import require_role
from app.helpers.search import DEFAULT_RESULT_LIMIT, MAX_RESULT_LIMIT
from app.helpers.search.text_utils import classify_query
from app.model import User
from app.schemas.search import TeacherSearchResponse, TeacherSearchResultItem
from app.services.search.teacher_search_service import TeacherSearchService

router = APIRouter(prefix="/teachers/search", tags=["Teacher Search"])


@router.get("", response_model=TeacherSearchResponse)
async def search_teachers(
    q: str = Query(..., min_length=1, description="Name, email, employee code, teacher ID, or phone"),
    limit: int = Query(DEFAULT_RESULT_LIMIT, ge=1, le=MAX_RESULT_LIMIT),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = TeacherSearchService(db)

    try:
        hits = service.search(q, limit=limit)
    except SearchValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    results = [
        TeacherSearchResultItem(
            display_name=hit.teacher.teacher_name,
            email=hit.teacher.user.email if hit.teacher.user else None,
            teacher_code=hit.teacher.employee_code or hit.teacher.teacher_id,
            internal_id=hit.teacher.teacher_id,
            department=hit.teacher.department,
            designation=hit.teacher.designation,
            phone=hit.teacher.user.phone if hit.teacher.user else None,
            profile_photo=hit.teacher.profile_photo,
            score=hit.confidence,
            confidence_label=hit.confidence_label,
            match_type=hit.match_type,
            matched_field=hit.matched_field,
            signals=hit.signals,
        )
        for hit in hits
    ]

    return TeacherSearchResponse(
        query=q,
        query_type=classify_query(q).value,
        result_count=len(results),
        results=results,
    )
