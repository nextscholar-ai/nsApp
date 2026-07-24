# from fastapi import APIRouter
# from fastapi import Depends
# from fastapi import HTTPException

# from sqlalchemy.orm import Session
# from sqlalchemy import func

# from app.dependencies import (
#     get_db,
#     get_current_student,
#     require_role
# )

# from app.model import (
#     User,
#     StudentProfile,
#     DailyClass,
#     Subject
# )

# from app.schemas import (
#     DailyClassCreate,
#     DailyClassResponse
# )


# router = APIRouter(
#     prefix="/daily-class",
#     tags=["Daily Class"]
# )


# # =====================================================
# # CREATE DAILY CLASS
# # Teacher/Admin Use
# # =====================================================

# @router.post(
#     "/{student_id}",
#     response_model=DailyClassResponse
# )
# def create_daily_class(

#     student_id: str,

#     data: DailyClassCreate,

#     current_user: User = Depends(
#         require_role(
#             "teacher",
#             "admin"
#         )
#     ),

#     db: Session = Depends(get_db)

# ):

#     student = (

#         db.query(StudentProfile)

#         .filter(
#             StudentProfile.student_id
#             == student_id
#         )

#         .first()
#     )

#     if not student:

#         raise HTTPException(
#             status_code=404,
#             detail="Student not found"
#         )

#     daily_class = DailyClass(

#         student_id=student.student_id,

#         subject_name=data.subject_name.strip().title(),

#         teacher_name=(
#             current_user.teacher_profile.teacher_name
#             if current_user.role == "teacher"
#             else data.teacher_name
#         ),

#         day_name=data.day_name,

#         class_date=data.class_date,

#         start_time=data.start_time,

#         end_time=data.end_time,

#         duration=data.duration,

#         attendance=data.attendance,

#         behaviour=data.behaviour
#     )

#     db.add(daily_class)

#     db.commit()

#     db.refresh(daily_class)

#     return daily_class


# # =====================================================
# # UPDATE DAILY CLASS
# # Teacher/Admin Use
# # =====================================================

# @router.put(
#     "/{class_id}",
#     response_model=DailyClassResponse
# )
# def update_daily_class(

#     class_id: int,

#     data: DailyClassCreate,

#     current_user: User = Depends(
#         require_role(
#             "teacher",
#             "admin"
#         )
#     ),

#     db: Session = Depends(get_db)

# ):

#     record = (

#         db.query(DailyClass)

#         .filter(
#             DailyClass.id == class_id
#         )

#         .first()
#     )

#     if not record:

#         raise HTTPException(
#             status_code=404,
#             detail="Class not found"
#         )

#     record.subject_name = data.subject_name.strip().title()
#     record.teacher_name = data.teacher_name
#     record.day_name = data.day_name
#     record.class_date = data.class_date
#     record.start_time = data.start_time
#     record.end_time = data.end_time
#     record.duration = data.duration
#     record.attendance = data.attendance
#     record.behaviour = data.behaviour

#     db.commit()

#     db.refresh(record)

#     return record


# # =====================================================
# # STUDENT VIEW ALL CLASSES
# # =====================================================

# @router.get(
#     "/my-classes",
#     response_model=list[DailyClassResponse]
# )
# def my_classes(

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     return (

#         db.query(DailyClass)

#         .filter(
#             DailyClass.student_id
#             == student.student_id
#         )

#         .order_by(
#             DailyClass.class_date.desc()
#         )

#         .all()
#     )


# # =====================================================
# # FILTER BY SUBJECT
# # =====================================================

# @router.get(
#     "/my-classes/{subject_name}",
#     response_model=list[DailyClassResponse]
# )
# def classes_by_subject(

#     subject_name: str,

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     return (

#         db.query(DailyClass)

#         .join(
#             Subject,
#             DailyClass.subject_name == Subject.subject_name
#         )


#         .filter(
#             DailyClass.student_id
#             == student.student_id,

#             func.lower(Subject.subject_name)
#             == subject_name.strip().lower()

#         )

#         .order_by(
#             DailyClass.class_date.desc()
#         )

#         .all()
#     )


# @router.get(
#     "/student/{student_id}",
#     response_model=list[
#         DailyClassResponse
#     ]
# )
# def get_student_classes(

#     student_id: str,

#     current_user: User = Depends(
#         require_role(
#             "teacher",
#             "admin"
#         )
#     ),

#     db: Session = Depends(get_db)

# ):

#     student = (

#         db.query(StudentProfile)

#         .filter(
#             StudentProfile.student_id
#             == student_id
#         )

#         .first()
#     )

#     if not student:

#         raise HTTPException(
#             status_code=404,
#             detail="Student not found"
#         )

#     return (

#         db.query(DailyClass)

#         .filter(
#             DailyClass.student_id
#             == student_id
#         )

#         .order_by(
#             DailyClass.class_date.desc()
#         )

#         .all()
#     )


# @router.delete(
#     "/{class_id}"
# )
# def delete_daily_class(

#     class_id: int,

#     current_user: User = Depends(
#         require_role(
#             "teacher",
#             "admin"
#         )
#     ),

#     db: Session = Depends(get_db)

# ):

#     record = (

#         db.query(DailyClass)

#         .filter(
#             DailyClass.id == class_id
#         )

#         .first()
#     )

#     if not record:

#         raise HTTPException(
#             status_code=404,
#             detail="Class not found"
#         )

#     if (

#         current_user.role == "teacher"

#         and

#         record.teacher_name
#         !=
#         current_user.teacher_profile.teacher_name

#     ):

#         raise HTTPException(
#             status_code=403,
#             detail="You can only delete your own classes"
#         )

#     db.delete(record)

#     db.commit()

#     return {
#         "message":
#         "Class deleted successfully"
#     }


# ============================================================
# routers/daily_class_routers.py - Daily Class Routes
# ============================================================

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import LectureStatus, UserRole
from app.dependencies import get_current_user, require_role
from app.model import (
    DailyClass,
    DailyClassStudent,
    StudentClass,
    TeacherProfile,
    TeacherSubject,
    User,
)
from app.schemas import (
    DailyClassCreate,
    DailyClassResponse,
    DailyClassStudentCreate,
    DailyClassStudentResponse,
    DailyClassUpdate,
)

router = APIRouter(prefix="/daily-class", tags=["Daily Class"])

# ============================================================
# DAILY CLASS CRUD
# ============================================================


@router.post("/", response_model=DailyClassResponse)
async def create_daily_class(
    class_data: DailyClassCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a daily class."""
    teacher = (
        db.query(TeacherProfile)
        .filter(TeacherProfile.user_id == current_user.id)
        .first()
    )

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    # Verify teacher is assigned to this class
    teacher_subject = (
        db.query(TeacherSubject)
        .filter(
            TeacherSubject.id == class_data.teacher_subject_id,
            TeacherSubject.teacher_id == teacher.teacher_id,
        )
        .first()
    )

    if not teacher_subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class",
        )

    # Check if class already exists for this date
    existing = (
        db.query(DailyClass)
        .filter(
            DailyClass.teacher_subject_id == class_data.teacher_subject_id,
            DailyClass.class_date == class_data.class_date,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class already exists for this date",
        )

    new_class = DailyClass(
        daily_class_id=class_data.daily_class_id,
        academic_sessions_id=class_data.academic_sessions_id,
        classroom_id=class_data.classroom_id,
        class_subject_id=class_data.class_subject_id,
        teacher_subject_id=class_data.teacher_subject_id,
        timetable_id=class_data.timetable_id,
        class_date=class_data.class_date,
        topic=class_data.topic,
        description=class_data.description,
        homework=class_data.homework,
        lecture_status=class_data.lecture_status,
        started_at=class_data.started_at,
        ended_at=class_data.ended_at,
        total_minutes=class_data.total_minutes,
        remarks=class_data.remarks,
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    return DailyClassResponse.model_validate(new_class)


@router.get("/classroom/{classroom_id}/summary")
async def get_class_summary(
    classroom_id: str,
    start_date: date,
    end_date: date,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get class summary for a date range."""
    classes = (
        db.query(DailyClass)
        .filter(
            DailyClass.classroom_id == classroom_id,
            DailyClass.class_date >= start_date,
            DailyClass.class_date <= end_date,
        )
        .all()
    )

    total_classes = len(classes)
    completed = len([c for c in classes if c.lecture_status == LectureStatus.COMPLETED])
    cancelled = len([c for c in classes if c.lecture_status == LectureStatus.CANCELLED])

    return {
        "classroom_id": classroom_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_classes": total_classes,
        "completed": completed,
        "cancelled": cancelled,
        "attendance_average": 0,
    }


@router.get("/", response_model=list[DailyClassResponse])
async def get_daily_classes(
    classroom_id: str | None = None,
    class_date: date | None = None,
    lecture_status: LectureStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get daily classes with filters."""
    query = db.query(DailyClass)

    if classroom_id:
        query = query.filter(DailyClass.classroom_id == classroom_id)

    if class_date:
        query = query.filter(DailyClass.class_date == class_date)

    if lecture_status:
        query = query.filter(DailyClass.lecture_status == lecture_status)

    if current_user.role == UserRole.TEACHER:
        teacher = (
            db.query(TeacherProfile)
            .filter(TeacherProfile.user_id == current_user.id)
            .first()
        )
        if teacher:
            teacher_subject_ids = db.query(TeacherSubject.id).filter(
                TeacherSubject.teacher_id == teacher.teacher_id,
            )
            query = query.filter(DailyClass.teacher_subject_id.in_(teacher_subject_ids))

    classes = query.order_by(DailyClass.class_date.desc()).all()
    return [DailyClassResponse.model_validate(c) for c in classes]


# ============================================================
# IMPORTANT: {daily_class_id} routes must come AFTER specific
# paths like /classroom/{classroom_id}/summary
# ============================================================


@router.get("/{daily_class_id}", response_model=DailyClassResponse)
async def get_daily_class(
    daily_class_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    daily_class = db.query(DailyClass).filter(DailyClass.id == daily_class_id).first()

    if not daily_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    return DailyClassResponse.model_validate(daily_class)


@router.post(
    "/{daily_class_id}/students",
    response_model=list[DailyClassStudentResponse],
)
async def mark_attendance(
    daily_class_id: int,
    attendance_data: list[DailyClassStudentCreate],
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    daily_class = db.query(DailyClass).filter(DailyClass.id == daily_class_id).first()

    if not daily_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    teacher = (
        db.query(TeacherProfile)
        .filter(TeacherProfile.user_id == current_user.id)
        .first()
    )

    if teacher and daily_class.teacher_subject_id != teacher.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark attendance for your classes",
        )

    marked_records = []
    for item in attendance_data:
        student_class = (
            db.query(StudentClass)
            .filter(
                StudentClass.id == item.student_class_id,
                StudentClass.classroom_id == daily_class.classroom_id,
            )
            .first()
        )

        if not student_class:
            continue

        existing = (
            db.query(DailyClassStudent)
            .filter(
                DailyClassStudent.daily_class_id == daily_class_id,
                DailyClassStudent.student_class_id == item.student_class_id,
            )
            .first()
        )

        if existing:
            existing.attendance_status = item.attendance_status
            existing.is_late = item.is_late
            existing.late_minutes = item.late_minutes
            existing.remarks = item.remarks
            existing.marked_by = current_user.id
            existing.marked_at = datetime.now(UTC)
            marked_records.append(existing)
        else:
            new_record = DailyClassStudent(
                daily_class_id=daily_class_id,
                student_class_id=item.student_class_id,
                attendance_status=item.attendance_status,
                is_late=item.is_late,
                late_minutes=item.late_minutes,
                remarks=item.remarks,
                marked_by=current_user.id,
            )
            db.add(new_record)
            marked_records.append(new_record)

    db.commit()

    return [DailyClassStudentResponse.model_validate(r) for r in marked_records]


@router.get(
    "/{daily_class_id}/students",
    response_model=list[DailyClassStudentResponse],
)
async def get_attendance(
    daily_class_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    daily_class = db.query(DailyClass).filter(DailyClass.id == daily_class_id).first()

    if not daily_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    attendance = (
        db.query(DailyClassStudent)
        .filter(DailyClassStudent.daily_class_id == daily_class_id)
        .all()
    )

    return [DailyClassStudentResponse.model_validate(a) for a in attendance]


@router.put("/{daily_class_id}", response_model=DailyClassResponse)
async def update_daily_class(
    daily_class_id: int,
    class_data: DailyClassUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    daily_class = db.query(DailyClass).filter(DailyClass.id == daily_class_id).first()

    if not daily_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    teacher = (
        db.query(TeacherProfile)
        .filter(TeacherProfile.user_id == current_user.id)
        .first()
    )

    if teacher and daily_class.teacher_subject_id != teacher.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own classes",
        )

    for key, value in class_data.dict(exclude_unset=True).items():
        setattr(daily_class, key, value)

    db.commit()
    db.refresh(daily_class)

    return DailyClassResponse.model_validate(daily_class)


@router.delete("/{daily_class_id}")
async def delete_daily_class(
    daily_class_id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    daily_class = db.query(DailyClass).filter(DailyClass.id == daily_class_id).first()

    if not daily_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    teacher = (
        db.query(TeacherProfile)
        .filter(TeacherProfile.user_id == current_user.id)
        .first()
    )

    if teacher and daily_class.teacher_subject_id != teacher.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own classes",
        )

    db.delete(daily_class)
    db.commit()

    return {"success": True, "message": "Class deleted successfully"}
