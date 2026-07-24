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
from app.schemas.search import StudentSearchDetail, StudentSearchResponse
from app.services.search.student_search_service import StudentSearchService

router = APIRouter(prefix="/students/search", tags=["Student Search"])


@router.get("", response_model=StudentSearchResponse)
async def search_students(
    q: Annotated[
        str,
        Query(
            min_length=1,
            description="Name, email, roll no., admission/registration number, or phone",
        ),
    ],
    limit: Annotated[int, Query(ge=1, le=MAX_RESULT_LIMIT)] = DEFAULT_RESULT_LIMIT,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: Session = Depends(get_db),
):
    """Always returns a ranked list of candidates (never auto-resolves a
    single "best" match, since names are never assumed unique) - the
    caller picks the right one and uses its `internal_id` with the
    existing student endpoints.
    """
    service = StudentSearchService(db)

    try:
        hits = service.search(q, limit=limit)
    except SearchValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    results = []
    for hit in hits:
        stu = hit.student
        sc = hit.student_class
        r = StudentSearchDetail(
            student_id=stu.student_id,
            admission_number=stu.admission_number,
            registration_number=stu.registration_number,
            student_name=stu.student_name,
            gender=stu.gender,
            date_of_birth=stu.date_of_birth,
            blood_group=stu.blood_group,
            profile_photo=stu.profile_photo,
            address=stu.address,
            city=stu.city,
            state=stu.state,
            pincode=stu.pincode,
            parent_name=stu.parent_name,
            parent_phone=stu.parent_phone,
            guardian_name=stu.guardian_name,
            guardian_phone=stu.guardian_phone,
            emergency_contact=stu.emergency_contact,
            admission_date=stu.admission_date,
            school_name=stu.school_name,
            medium=stu.medium,
            board=stu.board,
            remarks=stu.remarks,
            email=hit.student.user.email if hit.student.user else None,
            phone=hit.student.user.phone if hit.student.user else None,
            user_id=hit.student.user_id if hit.student else None,
            is_active=getattr(stu, "is_active", None),
            class_id=sc.classroom.class_code if sc and sc.classroom else None,
            class_name=sc.classroom.class_name if sc and sc.classroom else None,
            section=sc.classroom.section if sc and sc.classroom else None,
            display_name=sc.classroom.display_name if sc and sc.classroom else None,
            roll_number=sc.roll_number if sc else None,
            score=hit.confidence,
            confidence_label=hit.confidence_label,
            match_type=hit.match_type,
            matched_field=hit.matched_field,
            signals=hit.signals,
        )
        results.append(r)

    return StudentSearchResponse(
        query=q,
        query_type=classify_query(q).value,
        result_count=len(results),
        results=results,
    )
