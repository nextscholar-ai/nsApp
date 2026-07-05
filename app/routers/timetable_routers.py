# ============================================================
# routers/timetable_routers.py - Timetable & Availability Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.database import get_db
from app.model import User
from app.schemas import (
    WeekDayResponse, WeekDayCreate, TimeSlotResponse, TimeSlotCreate,
    ClassTimeTableResponse, ClassTimeTableCreate, ClassTimeTableUpdate,
    TeacherAvailabilityResponse, TeacherAvailabilityCreate, TeacherAvailabilityUpdate,
    ResponseSchema
)
from app.dependencies import get_current_user, require_role
from app.core.enums import UserRole
from app.services.academic_service import AcademicService

router = APIRouter(tags=["Timetable"])


# ==================== WEEK DAYS ====================

@router.get("/weekdays", response_model=List[WeekDayResponse])
async def get_weekdays(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all weekdays."""
    service = AcademicService(db)
    return service.get_all_weekdays()


@router.post("/weekdays", response_model=WeekDayResponse)
async def create_weekday(
    data: WeekDayCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a weekday."""
    service = AcademicService(db)
    return service.create_weekday(**data.dict())


# ==================== TIME SLOTS ====================

@router.get("/timeslots", response_model=List[TimeSlotResponse])
async def get_timeslots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all time slots."""
    service = AcademicService(db)
    return service.get_all_timeslots()


@router.post("/timeslots", response_model=TimeSlotResponse)
async def create_timeslot(
    data: TimeSlotCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a time slot."""
    service = AcademicService(db)
    return service.create_timeslot(**data.dict())


# ==================== TIMETABLE ====================

@router.get("/timetable/class/{classroom_id}", response_model=List[ClassTimeTableResponse])
async def get_class_timetable(
    classroom_id: int,
    session_id: int = Query(..., description="Academic session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get timetable for a class."""
    service = AcademicService(db)
    return service.get_class_timetable(classroom_id, session_id)


@router.post("/timetable", response_model=ClassTimeTableResponse)
async def create_timetable_entry(
    data: ClassTimeTableCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a timetable entry."""
    service = AcademicService(db)
    return service.create_timetable(**data.dict())


@router.delete("/timetable/{timetable_id}")
async def delete_timetable_entry(
    timetable_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Delete a timetable entry."""
    service = AcademicService(db)
    deleted = service.delete_timetable(timetable_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    return {"success": True, "message": "Timetable entry deleted"}


# ==================== TEACHER AVAILABILITY ====================

@router.get("/availability/teacher/{teacher_subject_id}", response_model=List[TeacherAvailabilityResponse])
async def get_teacher_availability(
    teacher_subject_id: int,
    session_id: int = Query(..., description="Academic session ID"),
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Get teacher availability."""
    service = AcademicService(db)
    return service.get_teacher_availability(teacher_subject_id, session_id)


@router.post("/availability", response_model=TeacherAvailabilityResponse)
async def create_availability(
    data: TeacherAvailabilityCreate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Create teacher availability."""
    service = AcademicService(db)
    return service.create_availability(**data.dict())


@router.put("/availability/{availability_id}", response_model=TeacherAvailabilityResponse)
async def update_availability(
    availability_id: int,
    data: TeacherAvailabilityUpdate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """Update teacher availability."""
    service = AcademicService(db)
    updated = service.update_availability(availability_id, **data.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Availability not found")
    return updated