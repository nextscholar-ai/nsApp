# ============================================================
# routers/student_routers.py - Student Routes
# ============================================================

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_student_profile, get_current_user, require_role
from app.model import (
    Assignment,
    AssignmentResult,
    DailyClassStudent,
    Exam,
    ExamResult,
    Fee,
    StudentClass,
    StudentProfile,
    User,
)
from app.schemas import (
    AssignmentResultResponse,
    ExamResultResponse,
    FeeResponse,
    StudentAttendanceResponse,
    StudentClassResponse,
    StudentProfileResponse,
    StudentProfileUpdate,
)

router = APIRouter(prefix="/student", tags=["Student"])

# ============================================================
# STUDENT PROFILE
# ============================================================


@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    student: Annotated[StudentProfile, Depends(get_current_student_profile)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get current student's profile."""
    return StudentProfileResponse.model_validate(student)


@router.put("/profile", response_model=StudentProfileResponse)
async def update_student_profile(
    profile_data: StudentProfileUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.STUDENT))],
    db: Annotated[Session, Depends(get_db)],
):
    """Update current student's profile."""
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    # Update fields
    for key, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)

    student.updated_by = current_user.id
    db.commit()
    db.refresh(student)

    return StudentProfileResponse.model_validate(student)


# ============================================================
# STUDENT PROFILE — ADMIN / STUDENT ACCESS BY student_id
# ============================================================


@router.get("/profile/{student_id}", response_model=StudentProfileResponse)
async def get_student_profile_by_id(
    student_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get a student profile by student_id.

    Access rules:
    - ADMIN  : can fetch any student profile.
    - STUDENT: can only fetch their own profile.
    - TEACHER: forbidden (403).
    """
    from app.core.enums import UserRole as _Role
    from app.services.identifier_resolver_service import IdentifierResolverService

    # Block teachers outright
    if current_user.role == _Role.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers cannot view student profiles via this endpoint",
        )

    # `student_id` ab id, email, ya naam - teeno accept karta hai
    profile = IdentifierResolverService(db).resolve_student(student_id)

    # Students can only view their own profile
    if current_user.role == _Role.STUDENT and profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile",
        )

    return StudentProfileResponse.model_validate(profile)


@router.put("/profile/{student_id}", response_model=StudentProfileResponse)
async def update_student_profile_by_id(
    student_id: str,
    profile_data: StudentProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update a student profile by student_id.

    Access rules:
    - STUDENT: can only update their own profile.
    - ADMIN   : forbidden — admins manage users, not student profiles directly.
    - TEACHER : forbidden.
    """
    from app.core.enums import UserRole as _Role
    from app.services.identifier_resolver_service import IdentifierResolverService

    # Only students may update student profiles
    if current_user.role != _Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can update student profiles",
        )

    # `student_id` ab id, email, ya naam - teeno accept karta hai
    profile = IdentifierResolverService(db).resolve_student(student_id)

    # Student can only update their own profile
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    for key, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)

    profile.updated_by = current_user.id
    db.commit()
    db.refresh(profile)

    return StudentProfileResponse.model_validate(profile)


# ============================================================
# STUDENT CLASSES
# ============================================================


@router.get("/classes", response_model=list[StudentClassResponse])
async def get_student_classes(
    academic_sessions_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """Get student's class enrollments."""
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    query = db.query(StudentClass).filter(StudentClass.student_id == student.student_id)

    if academic_sessions_id:
        query = query.filter(StudentClass.academic_sessions_id == academic_sessions_id)

    classes = query.order_by(StudentClass.academic_sessions_id.desc()).all()
    return [StudentClassResponse.model_validate(c) for c in classes]


# ============================================================
# STUDENT ATTENDANCE
# ============================================================


@router.get("/attendance/summary", response_model=StudentAttendanceResponse)
async def get_attendance_summary(
    academic_sessions_id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.STUDENT))],
    db: Annotated[Session, Depends(get_db)],
):
    """Get student's attendance summary."""
    from app.model import StudentAttendance

    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    student_class = (
        db.query(StudentClass)
        .filter(
            StudentClass.student_id == student.student_id,
            StudentClass.academic_sessions_id == academic_sessions_id,
        )
        .first()
    )

    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session",
        )

    attendance = (
        db.query(StudentAttendance)
        .filter(StudentAttendance.student_class_id == student_class.id)
        .first()
    )

    if not attendance:
        attendance = StudentAttendance(
            student_class_id=student_class.id,
            total_classes=0,
            present_classes=0,
            absent_classes=0,
            attendance_percentage=0.0,
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)

    return StudentAttendanceResponse.model_validate(attendance)


@router.get("/attendance/daily", response_model=list[dict])
async def get_daily_attendance(
    academic_sessions_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """Get student's daily attendance records."""
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    student_class = (
        db.query(StudentClass)
        .filter(
            StudentClass.student_id == student.student_id,
            StudentClass.academic_sessions_id == academic_sessions_id,
        )
        .first()
    )

    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session",
        )

    query = db.query(DailyClassStudent).filter(
        DailyClassStudent.student_class_id == student_class.id,
    )

    if start_date:
        query = query.filter(DailyClassStudent.created_at >= start_date)
    if end_date:
        query = query.filter(DailyClassStudent.created_at <= end_date)

    records = query.order_by(DailyClassStudent.created_at.desc()).all()

    return [
        {
            "date": r.created_at.date(),
            "status": r.attendance_status,
            "is_late": r.is_late,
            "late_minutes": r.late_minutes,
            "remarks": r.remarks,
        }
        for r in records
    ]


# ============================================================
# STUDENT ASSIGNMENTS
# ============================================================


@router.get("/assignments", response_model=list[AssignmentResultResponse])
async def get_student_assignments(
    academic_sessions_id: int,
    subject_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """Get student's assignment results."""
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    student_class = (
        db.query(StudentClass)
        .filter(
            StudentClass.student_id == student.student_id,
            StudentClass.academic_sessions_id == academic_sessions_id,
        )
        .first()
    )

    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session",
        )

    query = db.query(AssignmentResult).filter(
        AssignmentResult.student_class_id == student_class.id,
    )

    if subject_id:
        query = query.join(Assignment).filter(Assignment.class_subject_id == subject_id)

    results = query.order_by(AssignmentResult.created_at.desc()).all()
    return [AssignmentResultResponse.model_validate(r) for r in results]


# ============================================================
# STUDENT EXAMS
# ============================================================


@router.get("/exams", response_model=list[ExamResultResponse])
async def get_student_exams(
    academic_sessions_id: int,
    subject_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """Get student's exam results."""
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    student_class = (
        db.query(StudentClass)
        .filter(
            StudentClass.student_id == student.student_id,
            StudentClass.academic_sessions_id == academic_sessions_id,
        )
        .first()
    )

    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session",
        )

    query = db.query(ExamResult).filter(ExamResult.student_class_id == student_class.id)

    if subject_id:
        query = query.join(Exam).filter(Exam.class_subject_id == subject_id)

    results = query.order_by(ExamResult.created_at.desc()).all()
    return [ExamResultResponse.model_validate(r) for r in results]


# ============================================================
# STUDENT FEES
# ============================================================


@router.get("/fees", response_model=list[FeeResponse])
async def get_student_fees(
    academic_sessions_id: str,
    fee_status: Annotated[str | None, Query(alias="status")] = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """Get student's fee records."""
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    student_class = (
        db.query(StudentClass)
        .filter(
            StudentClass.student_id == student.student_id,
            StudentClass.academic_sessions_id == academic_sessions_id,
        )
        .first()
    )

    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session",
        )

    query = db.query(Fee).filter(Fee.student_class_id == student_class.id)

    if fee_status:
        query = query.filter(Fee.status == fee_status)

    fees = query.order_by(Fee.fee_year.desc(), Fee.fee_month.desc()).all()
    return [FeeResponse.model_validate(f) for f in fees]


@router.get("/fees/summary")
async def get_fee_summary(
    academic_sessions_id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.STUDENT))],
    db: Annotated[Session, Depends(get_db)],
):
    """Get student's fee summary."""
    student = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    student_class = (
        db.query(StudentClass)
        .filter(
            StudentClass.student_id == student.student_id,
            StudentClass.academic_sessions_id == academic_sessions_id,
        )
        .first()
    )

    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session",
        )

    fees = db.query(Fee).filter(Fee.student_class_id == student_class.id).all()

    total_amount = sum(f.total_amount for f in fees)
    paid_amount = sum(f.paid_amount for f in fees)
    pending_amount = total_amount - paid_amount

    return {
        "total_amount": float(total_amount),
        "paid_amount": float(paid_amount),
        "pending_amount": float(pending_amount),
        "status": "Paid" if pending_amount == 0 else "Pending",
    }
