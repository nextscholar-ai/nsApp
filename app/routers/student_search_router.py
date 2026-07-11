# ============================================================
# app/routers/student_search_router.py
# ============================================================
#
# Natural-language search endpoint for students: name, email, roll/
# admission/registration number, or phone in -> ranked list of
# candidates out. This is ADDITIVE: every existing ID-based student
# endpoint (student_routers.py) is untouched. Resolve "which student did
# the user mean?" here, then use the returned internal_id with the
# existing endpoints.
#
# Access: Admin and Teacher only (searching across the whole student
# body is a staff operation; a student searching for classmates by name
# is a privacy consideration this project doesn't currently have a
# policy for, so it's deliberately excluded until that's decided).

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.core.exceptions import SearchValidationError
from app.dependencies import require_role
from app.helpers.search import DEFAULT_RESULT_LIMIT, MAX_RESULT_LIMIT
from app.helpers.search.text_utils import classify_query
from app.model import User
from app.schemas.search import StudentSearchResponse, StudentSearchResultItem
from app.services.search.student_search_service import StudentSearchService

router = APIRouter(prefix="/students/search", tags=["Student Search"])


@router.get("", response_model=StudentSearchResponse)
async def search_students(
    q: str = Query(..., min_length=1, description="Name, email, roll no., admission/registration number, or phone"),
    limit: int = Query(DEFAULT_RESULT_LIMIT, ge=1, le=MAX_RESULT_LIMIT),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: Session = Depends(get_db),
):
    """Always returns a ranked list of candidates (never auto-resolves a
    single "best" match, since names are never assumed unique) - the
    caller picks the right one and uses its `internal_id` with the
    existing student endpoints."""
    service = StudentSearchService(db)

    try:
        hits = service.search(q, limit=limit)
    except SearchValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    results = [
        StudentSearchResultItem(
            display_name=hit.student.student_name,
            email=hit.student.user.email if hit.student.user else None,
            student_code=hit.student.admission_number,
            internal_id=hit.student.student_id,
            registration_number=hit.student.registration_number,
            phone=hit.student.user.phone if hit.student.user else None,
            profile_photo=hit.student.profile_photo,
            score=hit.confidence,
            confidence_label=hit.confidence_label,
            match_type=hit.match_type,
            matched_field=hit.matched_field,
            signals=hit.signals,
        )
        for hit in hits
    ]

    return StudentSearchResponse(
        query=q,
        query_type=classify_query(q).value,
        result_count=len(results),
        results=results,
    )
