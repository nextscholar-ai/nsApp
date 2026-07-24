# ============================================================
# app/routers/teacher_search_router.py
# ============================================================
#
# Natural-language search endpoint for teachers, mirroring
# student_search_router.py. ADDITIVE: existing ID-based teacher
# endpoints (teacher_router.py) are untouched.
#
# Access: Admin only (staff-directory lookup).

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.core.exceptions import SearchValidationError
from app.dependencies import require_role
from app.helpers.search import DEFAULT_RESULT_LIMIT, MAX_RESULT_LIMIT
from app.helpers.search.text_utils import classify_query
from app.model import User
from app.schemas.search import TeacherSearchDetail, TeacherSearchResponse
from app.services.search.teacher_search_service import TeacherSearchService

router = APIRouter(prefix="/teachers/search", tags=["Teacher Search"])


@router.get("", response_model=TeacherSearchResponse)
async def search_teachers(
    q: Annotated[
        str,
        Query(
            min_length=1, description="Name, email, employee code, teacher ID, or phone"
        ),
    ],
    limit: Annotated[int, Query(ge=1, le=MAX_RESULT_LIMIT)] = DEFAULT_RESULT_LIMIT,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = TeacherSearchService(db)

    try:
        hits = service.search(q, limit=limit)
    except SearchValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    results = []
    for hit in hits:
        t = hit.teacher
        r = TeacherSearchDetail(
            teacher_id=t.teacher_id,
            employee_code=t.employee_code,
            teacher_name=t.teacher_name,
            gender=t.gender,
            date_of_birth=t.date_of_birth,
            qualification=t.qualification,
            experience_years=t.experience_years,
            specialization=t.specialization,
            profile_photo=t.profile_photo,
            joining_date=t.joining_date,
            designation=t.designation,
            department=t.department,
            address=t.address,
            city=t.city,
            state=t.state,
            pincode=t.pincode,
            emergency_contact=t.emergency_contact,
            remarks=t.remarks,
            email=t.user.email if t.user else None,
            phone=t.user.phone if t.user else None,
            user_id=t.user_id if t else None,
            is_active=getattr(t, "is_active", None),
            subjects=hit.subjects,
            class_teacher_of=hit.class_teacher_of,
            score=hit.confidence,
            confidence_label=hit.confidence_label,
            match_type=hit.match_type,
            matched_field=hit.matched_field,
            signals=hit.signals,
        )
        results.append(r)

    return TeacherSearchResponse(
        query=q,
        query_type=classify_query(q).value,
        result_count=len(results),
        results=results,
    )
