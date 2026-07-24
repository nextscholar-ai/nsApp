from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_user, require_role
from app.model import StudentTopicProgressReport, Topic, TopicProgress, User
from app.schemas.topic import (
    StudentTopicProgressReportCreate,
    StudentTopicProgressReportResponse,
    TopicCreate,
    TopicProgressCreate,
    TopicProgressResponse,
    TopicResponse,
)

router = APIRouter(prefix="/topics", tags=["Topics"])

# ============================================================
# IMPORTANT: Specific sub-paths MUST be defined BEFORE /{id}
# parameterized routes, otherwise FastAPI matches "progress"
# as a literal value for {id}.
# ============================================================

# ==================== TOPIC PROGRESS (ka_topic_progress) ====================


@router.get("/progress", response_model=list[TopicProgressResponse])
async def list_topic_progress(
    student_id: str | None = None,
    topic_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(TopicProgress)
    if student_id:
        query = query.filter(TopicProgress.student_id == student_id)
    if topic_id:
        query = query.filter(TopicProgress.topic_id == topic_id)
    return query.order_by(TopicProgress.date.desc()).all()


@router.post("/progress", response_model=TopicProgressResponse, status_code=201)
async def create_topic_progress(
    data: TopicProgressCreate,
    current_user: Annotated[
        User, Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    tp = TopicProgress(**data.model_dump())
    db.add(tp)
    db.commit()
    db.refresh(tp)
    return tp


@router.get("/progress/{id}", response_model=TopicProgressResponse)
async def get_topic_progress(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    tp = db.query(TopicProgress).filter(TopicProgress.topic_progress_code == id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="Topic progress not found")
    return tp


@router.put("/progress/{id}", response_model=TopicProgressResponse)
async def update_topic_progress(
    id: str,
    data: TopicProgressCreate,
    current_user: Annotated[
        User, Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    tp = db.query(TopicProgress).filter(TopicProgress.topic_progress_code == id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="Topic progress not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tp, key, value)
    db.commit()
    db.refresh(tp)
    return tp


@router.delete("/progress/{id}")
async def delete_topic_progress(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    tp = db.query(TopicProgress).filter(TopicProgress.topic_progress_code == id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="Topic progress not found")
    db.delete(tp)
    db.commit()
    return {"success": True, "message": "Topic progress deleted"}


# ==================== STUDENT TOPIC PROGRESS REPORT ====================


@router.get(
    "/progress-reports",
    response_model=list[StudentTopicProgressReportResponse],
)
async def list_student_topic_progress_reports(
    report_id: str | None = None,
    topic_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(StudentTopicProgressReport)
    if report_id:
        query = query.filter(StudentTopicProgressReport.report_id == report_id)
    if topic_id:
        query = query.filter(StudentTopicProgressReport.topic_id == topic_id)
    return query.all()


@router.post(
    "/progress-reports",
    response_model=StudentTopicProgressReportResponse,
    status_code=201,
)
async def create_student_topic_progress_report(
    data: StudentTopicProgressReportCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    report = StudentTopicProgressReport(**data.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/progress-reports/{id}", response_model=StudentTopicProgressReportResponse)
async def get_student_topic_progress_report(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    report = (
        db.query(StudentTopicProgressReport)
        .filter(StudentTopicProgressReport.topic_progress_report_code == id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Progress report not found")
    return report


@router.delete("/progress-reports/{id}")
async def delete_student_topic_progress_report(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    report = (
        db.query(StudentTopicProgressReport)
        .filter(StudentTopicProgressReport.id == id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Progress report not found")
    db.delete(report)
    db.commit()
    return {"success": True, "message": "Progress report deleted"}


# ==================== TOPICS (ka_topic) ====================


@router.get("", response_model=list[TopicResponse])
async def list_topics(
    course_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Topic)
    if course_id:
        query = query.filter(Topic.course_id == course_id)
    return query.order_by(Topic.topic_name).all()


@router.post("", response_model=TopicResponse, status_code=201)
async def create_topic(
    data: TopicCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    existing = db.query(Topic).filter(Topic.topic_id == data.topic_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Topic with this ID already exists")
    topic = Topic(**data.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.get("/{id}", response_model=TopicResponse)
async def get_topic(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    topic = db.query(Topic).filter(Topic.topic_code == id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.put("/{id}", response_model=TopicResponse)
async def update_topic(
    id: str,
    data: TopicCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    topic = db.query(Topic).filter(Topic.topic_code == id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, key, value)
    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/{id}")
async def delete_topic(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    topic = db.query(Topic).filter(Topic.topic_code == id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"success": True, "message": "Topic deleted"}
