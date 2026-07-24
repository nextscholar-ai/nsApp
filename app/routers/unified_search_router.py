from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_user, require_role
from app.helpers.search import normalize_text
from app.model import (
    ClassRoom,
    Notice,
    StudentClass,
    StudentProfile,
    Subject,
    TeacherProfile,
    Topic,
    User,
    ZoomMeeting,
)

router = APIRouter(prefix="/search", tags=["Universal Search"])


class SearchResultItem:
    def __init__(self, entity_type, id, name, subtitle, details) -> None:
        self.entity_type = entity_type
        self.id = id
        self.name = name
        self.subtitle = subtitle
        self.details = details


class SearchResultItemSchema(BaseModel):
    entity_type: str = Field(
        ...,
        description='"student" | "teacher" | "classroom" | "subject" | "notice" | "zoom" | "topic"',
    )
    id: str = Field(..., description="Unique identifier for the entity")
    name: str = Field(..., description="Display name")
    subtitle: str | None = Field(
        None,
        description="Secondary info (class, department, etc.)",
    )
    details: dict = Field(default_factory=dict, description="Full entity details")


class UniversalSearchResponse(BaseModel):
    query: str
    result_count: int
    results: list[SearchResultItemSchema]


@router.get("/universal", response_model=UniversalSearchResponse)
async def universal_search(
    q: Annotated[
        str,
        Query(
            min_length=1,
            description="Search across all entities: students, teachers, classes, subjects, notices, zoom meetings, topics",
        ),
    ],
    limit: Annotated[
        int, Query(ge=1, le=20, description="Results per entity type")
    ] = 5,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
    db: Session = Depends(get_db),
):
    """Search everything at once: students, teachers, classrooms,
    subjects, notices, zoom meetings, and topics. Results are grouped
    by entity type with a maximum of `limit` per type.
    """
    raw = q.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    normalized = normalize_text(raw)
    results = []

    pattern = f"%{normalized}%"

    # 1. Students
    students = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.student_class).joinedload(StudentClass.classroom),
        )
        .filter(
            StudentProfile.is_active,
            or_(
                StudentProfile.student_name.ilike(pattern),
                StudentProfile.student_id.ilike(pattern),
                StudentProfile.admission_number.ilike(pattern),
                StudentProfile.registration_number.ilike(pattern),
                StudentProfile.parent_name.ilike(pattern),
                StudentProfile.guardian_name.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results.extend(
        [
            SearchResultItemSchema(
                entity_type="student",
                id=s.student_id,
                name=s.student_name,
                subtitle=(
                    sc.classroom.display_name
                    if (sc := s.student_class[0] if s.student_class else None)
                    and sc.classroom
                    else "N/A"
                ),
                details={
                    "student_id": s.student_id,
                    "student_name": s.student_name,
                    "admission_number": s.admission_number,
                    "registration_number": s.registration_number,
                    "email": s.user.email if s.user else None,
                    "phone": s.user.phone if s.user else None,
                    "class_name": sc.classroom.class_name
                    if sc and sc.classroom
                    else None,
                    "section": sc.classroom.section if sc and sc.classroom else None,
                    "roll_number": sc.roll_number if sc else None,
                    "parent_name": s.parent_name,
                    "guardian_name": s.guardian_name,
                    "profile_photo": s.profile_photo,
                },
            )
            for s in students
        ]
    )

    # 2. Teachers
    teachers = (
        db.query(TeacherProfile)
        .options(joinedload(TeacherProfile.user))
        .filter(
            TeacherProfile.is_active,
            or_(
                TeacherProfile.teacher_name.ilike(pattern),
                TeacherProfile.teacher_id.ilike(pattern),
                TeacherProfile.employee_code.ilike(pattern),
                TeacherProfile.department.ilike(pattern),
                TeacherProfile.designation.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results.extend(
        [
            SearchResultItemSchema(
                entity_type="teacher",
                id=t.teacher_id,
                name=t.teacher_name,
                subtitle=t.department or t.designation or "N/A",
                details={
                    "teacher_id": t.teacher_id,
                    "teacher_name": t.teacher_name,
                    "employee_code": t.employee_code,
                    "email": t.user.email if t.user else None,
                    "phone": t.user.phone if t.user else None,
                    "department": t.department,
                    "designation": t.designation,
                    "qualification": t.qualification,
                    "specialization": t.specialization,
                    "experience_years": t.experience_years,
                    "profile_photo": t.profile_photo,
                },
            )
            for t in teachers
        ]
    )

    # 3. Classrooms
    classrooms = (
        db.query(ClassRoom)
        .filter(
            ClassRoom.is_active,
            or_(
                ClassRoom.class_name.ilike(pattern),
                ClassRoom.class_code.ilike(pattern),
                ClassRoom.section.ilike(pattern),
                ClassRoom.display_name.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results.extend(
        [
            SearchResultItemSchema(
                entity_type="classroom",
                id=str(c.class_code),
                name=c.display_name,
                subtitle=f"{c.class_code} | {c.class_name}-{c.section}",
                details={
                    "id": c.class_code,
                    "class_code": c.class_code,
                    "class_name": c.class_name,
                    "section": c.section,
                    "display_name": c.display_name,
                    "academic_sessions_id": c.academic_sessions_id,
                    "class_teacher_id": c.class_teacher_id,
                },
            )
            for c in classrooms
        ]
    )

    # 4. Subjects
    subjects = (
        db.query(Subject)
        .filter(
            Subject.is_active,
            or_(
                Subject.subject_name.ilike(pattern),
                Subject.subject_code.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results.extend(
        [
            SearchResultItemSchema(
                entity_type="subject",
                id=str(s.subject_code),
                name=s.subject_name,
                subtitle=s.subject_code,
                details={
                    "id": s.subject_code,
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "subject_type": s.subject_type,
                },
            )
            for s in subjects
        ]
    )

    # 5. Notices
    notices = (
        db.query(Notice)
        .filter(
            or_(
                Notice.title.ilike(pattern),
                Notice.description.ilike(pattern),
                Notice.notice_code.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results.extend(
        [
            SearchResultItemSchema(
                entity_type="notice",
                id=n.notice_code,
                name=n.title,
                subtitle=n.notice_type.value
                if hasattr(n.notice_type, "value")
                else str(n.notice_type),
                details={
                    "notice_id": n.notice_code,
                    "title": n.title,
                    "description": n.description[:200] + "..."
                    if n.description and len(n.description) > 200
                    else n.description,
                    "notice_type": n.notice_type.value
                    if hasattr(n.notice_type, "value")
                    else str(n.notice_type),
                    "audience": n.audience.value
                    if hasattr(n.audience, "value")
                    else str(n.audience),
                    "publish_date": str(n.publish_date) if n.publish_date else None,
                    "is_pinned": n.is_pinned,
                },
            )
            for n in notices
        ]
    )

    # 6. Zoom meetings
    zoom_meetings = (
        db.query(ZoomMeeting)
        .filter(
            or_(
                ZoomMeeting.topic.ilike(pattern),
                ZoomMeeting.uuid.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results.extend(
        [
            SearchResultItemSchema(
                entity_type="zoom",
                id=z.uuid,
                name=z.topic or "Untitled Meeting",
                subtitle=f"ID: {z.meeting_id} | {str(z.start_time)[:10] if z.start_time else 'N/A'}",
                details={
                    "uuid": z.uuid,
                    "meeting_id": z.meeting_id,
                    "topic": z.topic,
                    "start_time": str(z.start_time) if z.start_time else None,
                    "duration": z.duration,
                    "timezone": z.timezone,
                    "recording_count": z.recording_count,
                    "share_url": z.share_url,
                },
            )
            for z in zoom_meetings
        ]
    )

    # 7. Topics
    topics = (
        db.query(Topic)
        .options(joinedload(Topic.course))
        .filter(
            or_(
                Topic.topic_name.ilike(pattern),
                Topic.topic_id.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results.extend(
        [
            SearchResultItemSchema(
                entity_type="topic",
                id=str(t.topic_code),
                name=t.topic_name or "Untitled",
                subtitle=t.topic_id or "",
                details={
                    "id": t.topic_code,
                    "topic_id": t.topic_id,
                    "topic_name": t.topic_name,
                    "course_id": t.course_id,
                    "course_name": t.course.course_name if t.course else None,
                },
            )
            for t in topics
        ]
    )

    return UniversalSearchResponse(
        query=q,
        result_count=len(results),
        results=results,
    )


@router.get("/classrooms", response_model=UniversalSearchResponse)
async def search_classrooms(
    q: Annotated[
        str,
        Query(min_length=1, description="Search classrooms by name, code, or section"),
    ],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw = q.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    normalized = normalize_text(raw)
    pattern = f"%{normalized}%"
    classrooms = (
        db.query(ClassRoom)
        .filter(
            ClassRoom.is_active,
            or_(
                ClassRoom.class_name.ilike(pattern),
                ClassRoom.class_code.ilike(pattern),
                ClassRoom.section.ilike(pattern),
                ClassRoom.display_name.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results = [
        SearchResultItemSchema(
            entity_type="classroom",
            id=str(c.class_code),
            name=c.display_name,
            subtitle=f"{c.class_code} | {c.class_name}-{c.section}",
            details={
                "id": c.class_code,
                "class_code": c.class_code,
                "class_name": c.class_name,
                "section": c.section,
                "display_name": c.display_name,
                "academic_sessions_id": c.academic_sessions_id,
                "class_teacher_id": c.class_teacher_id,
            },
        )
        for c in classrooms
    ]
    return UniversalSearchResponse(query=q, result_count=len(results), results=results)


@router.get("/notices", response_model=UniversalSearchResponse)
async def search_notices(
    q: Annotated[
        str,
        Query(min_length=1, description="Search notices by title, description, or ID"),
    ],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw = q.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    normalized = normalize_text(raw)
    pattern = f"%{normalized}%"
    notices = (
        db.query(Notice)
        .filter(
            or_(
                Notice.title.ilike(pattern),
                Notice.description.ilike(pattern),
                Notice.notice_code.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results = [
        SearchResultItemSchema(
            entity_type="notice",
            id=n.notice_id,
            name=n.title,
            subtitle=n.notice_type.value
            if hasattr(n.notice_type, "value")
            else str(n.notice_type),
            details={
                "notice_id": n.notice_id,
                "title": n.title,
                "description": n.description[:200] + "..."
                if n.description and len(n.description) > 200
                else n.description,
                "notice_type": n.notice_type.value
                if hasattr(n.notice_type, "value")
                else str(n.notice_type),
                "audience": n.audience.value
                if hasattr(n.audience, "value")
                else str(n.audience),
                "publish_date": str(n.publish_date) if n.publish_date else None,
                "expiry_date": str(n.expiry_date) if n.expiry_date else None,
                "is_pinned": n.is_pinned,
                "attachment_name": n.attachment_name,
            },
        )
        for n in notices
    ]
    return UniversalSearchResponse(query=q, result_count=len(results), results=results)


@router.get("/subjects", response_model=UniversalSearchResponse)
async def search_subjects(
    q: Annotated[
        str, Query(min_length=1, description="Search subjects by name or code")
    ],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw = q.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    normalized = normalize_text(raw)
    pattern = f"%{normalized}%"
    subjects = (
        db.query(Subject)
        .filter(
            Subject.is_active,
            or_(
                Subject.subject_name.ilike(pattern),
                Subject.subject_code.ilike(pattern),
            ),
        )
        .limit(limit)
        .all()
    )
    results = [
        SearchResultItemSchema(
            entity_type="subject",
            id=str(s.subject_code),
            name=s.subject_name,
            subtitle=s.subject_code,
            details={
                "id": s.subject_code,
                "subject_code": s.subject_code,
                "subject_name": s.subject_name,
                "subject_type": s.subject_type,
                "display_order": s.display_order,
            },
        )
        for s in subjects
    ]
    return UniversalSearchResponse(query=q, result_count=len(results), results=results)
