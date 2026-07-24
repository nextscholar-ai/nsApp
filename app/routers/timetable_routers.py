# ============================================================
# routers/timetable_routers.py - Timetable & Availability Routes
# ============================================================

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_user, require_role
from app.model import User
from app.schemas import (
    ClassTimeTableCreate,
    ClassTimeTableResponse,
    ClassTimeTableUpdate,
    StudentTimetableItemResponse,
    TeacherAvailabilityCreate,
    TeacherAvailabilityResponse,
    TeacherAvailabilityUpdate,
    TeacherTimetableItemResponse,
    TimeSlotCreate,
    TimeSlotResponse,
    WeekDayCreate,
    WeekDayResponse,
)
from app.services.academic_service import AcademicService

router = APIRouter(tags=["Timetable"])


# ==================== WEEK DAYS ====================


@router.get("/weekdays", response_model=list[WeekDayResponse])
async def get_weekdays(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get all weekdays."""
    service = AcademicService(db)
    return service.get_all_weekdays()


@router.post("/weekdays", response_model=WeekDayResponse)
async def create_weekday(
    data: WeekDayCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a weekday."""
    service = AcademicService(db)
    return service.create_weekday(**data.model_dump())


# ==================== TIME SLOTS ====================


@router.get("/timeslots", response_model=list[TimeSlotResponse])
async def get_timeslots(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get all time slots."""
    service = AcademicService(db)
    return service.get_all_timeslots()


@router.post("/timeslots", response_model=TimeSlotResponse)
async def create_timeslot(
    data: TimeSlotCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a time slot."""
    service = AcademicService(db)
    return service.create_timeslot(**data.model_dump())


# ==================== TIMETABLE ====================


@router.get(
    "/timetable/class/{classroom_id}",
    response_model=list[ClassTimeTableResponse],
)
async def get_class_timetable(
    classroom_id: int,
    session_id: Annotated[int, Query(description="Academic session ID")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get timetable for a class."""
    service = AcademicService(db)
    return service.get_class_timetable(classroom_id, session_id)


# ==================== ADMIN TIMETABLE LIST ====================


@router.get("/timetables")
async def admin_get_timetables(
    class_id: Annotated[int | None, Query(alias="class")] = None,
    teacher_subject_id: Annotated[int | None, Query(alias="teacher")] = None,
    subject_id: Annotated[int | None, Query(alias="subject")] = None,
    day_id: Annotated[int | None, Query(alias="day")] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin: list timetable entries with optional filters."""
    from app.schemas import ClassTimeTableResponse
    from app.services.timetable_service import TimetableService

    service = TimetableService(db)
    entries = service.admin_get_timetables(
        classroom_id=class_id,
        teacher_subject_id=teacher_subject_id,
        class_subject_id=subject_id,
        week_day_id=day_id,
    )
    return [ClassTimeTableResponse.model_validate(e) for e in entries]


@router.post("/timetable", response_model=ClassTimeTableResponse)
async def create_timetable_entry(
    data: ClassTimeTableCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a timetable entry."""
    service = AcademicService(db)
    return service.create_timetable(**data.model_dump())


@router.put("/timetable/{id}", response_model=ClassTimeTableResponse)
async def update_timetable_entry(
    id: int,
    data: ClassTimeTableUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Admin: Update a timetable entry."""
    from app.services.timetable_service import TimetableService

    service = TimetableService(db)
    updated = service.admin_update_timetable(id, data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    return updated


@router.delete("/timetable/{id}")
async def delete_timetable_entry(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    """Admin: Delete a timetable entry."""
    from app.services.timetable_service import TimetableService

    service = TimetableService(db)
    deleted = service.admin_delete_timetable(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    return {"success": True, "message": "Timetable entry deleted"}


# ==================== STUDENT TIMETABLE ====================


@router.get("/student/timetable", response_model=list[StudentTimetableItemResponse])
async def get_student_timetable(
    current_user: Annotated[User, Depends(require_role(UserRole.STUDENT))],
    db: Annotated[Session, Depends(get_db)],
):
    """Student: get ONLY own class timetable for current academic session."""
    from app.services.timetable_service import TimetableService

    service = TimetableService(db)
    return service.student_get_timetable(student_user_id=current_user.id)


# ==================== TEACHER TIMETABLE ====================


@router.get("/teacher/timetable", response_model=list[TeacherTimetableItemResponse])
async def get_teacher_timetable(
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Teacher: get timetable for assigned classes for current academic session."""
    from app.services.timetable_service import TimetableService

    service = TimetableService(db)
    return service.teacher_get_timetable(teacher_user_id=current_user.id)


# ==================== TEACHER AVAILABILITY ====================


@router.get(
    "/availability/teacher/{teacher_subject_id}",
    response_model=list[TeacherAvailabilityResponse],
)
async def get_teacher_availability(
    teacher_subject_id: int,
    session_id: Annotated[int, Query(description="Academic session ID")],
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Get teacher availability."""
    service = AcademicService(db)
    return service.get_teacher_availability(teacher_subject_id, session_id)


@router.post("/availability", response_model=TeacherAvailabilityResponse)
async def create_availability(
    data: TeacherAvailabilityCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Create teacher availability."""
    service = AcademicService(db)
    return service.create_availability(**data.model_dump())


@router.put(
    "/availability/{availability_id}",
    response_model=TeacherAvailabilityResponse,
)
async def update_availability(
    availability_id: int,
    data: TeacherAvailabilityUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Update teacher availability."""
    service = AcademicService(db)
    updated = service.update_availability(
        availability_id,
        **data.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Availability not found")
    return updated
