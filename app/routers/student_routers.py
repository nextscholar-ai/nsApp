# from fastapi import APIRouter
# from fastapi import Depends

# from app.model import (
#     User,
#     StudentProfile
# )

# from app.dependencies import (
#     require_role,
#     get_current_student
# )

# router = APIRouter(
#     prefix="/student",
#     tags=["Student"]
# )


# # =====================================================
# # STUDENT DASHBOARD
# # =====================================================

# @router.get("/dashboard")
# def student_dashboard(

#     current_user: User = Depends(
#         require_role("student")
#     ),

#     student: StudentProfile = Depends(
#         get_current_student
#     )
# ):

#     return {

#         "student_id":
#         student.student_id,

#         "student_name":
#         student.student_name,

#         "student_email":
#         student.student_email,

#         "student_phone":
#         student.student_phone,

#         "student_class":
#         student.student_class,

#         "role":
#         current_user.role,

#         "is_active":
#         current_user.is_active
#     }


# # =====================================================
# # STUDENT PROFILE SUMMARY
# # =====================================================

# @router.get("/me")
# def get_my_profile(

#     current_user: User = Depends(
#         require_role("student")
#     ),

#     student: StudentProfile = Depends(
#         get_current_student
#     )
# ):

#     return {

#         "student_id":
#         student.student_id,

#         "student_name":
#         student.student_name,

#         "student_email":
#         student.student_email,

#         "student_phone":
#         student.student_phone,

#         "student_class":
#         student.student_class,

#         "parent_name":
#         student.parent_name,

#         "parent_phone":
#         student.parent_phone,

#         "guardian_name":
#         student.guardian_name,

#         "guardian_phone":
#         student.guardian_phone,

#         "school_name":
#         student.school_name,

#         "medium":
#         student.medium,

#         "board":
#         student.board,

#         "role":
#         current_user.role
#     }


# ============================================================
# routers/student_routers.py - Student Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.database import get_db
from app.model import User, StudentProfile, StudentClass, DailyClassStudent,Assignment, AssignmentResult, Exam, ExamResult, Fee
from app.schemas import (
    StudentProfileResponse,
    StudentProfileUpdate,
    StudentClassResponse,
    StudentAttendanceResponse,
    AssignmentResultResponse,
    ExamResultResponse,
    FeeResponse,
    ResponseSchema,
    PaginatedResponseSchema
)
from app.dependencies import (
    get_current_user,
    get_current_student_profile,
    require_role
)
from app.core.enums import UserRole

router = APIRouter(prefix="/student", tags=["Student"])

# ============================================================
# STUDENT PROFILE
# ============================================================

@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db)
):
    """
    Get current student's profile.
    """
    return StudentProfileResponse.model_validate(student)

@router.put("/profile", response_model=StudentProfileResponse)
async def update_student_profile(
    profile_data: StudentProfileUpdate,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Update current student's profile.
    """
    student = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Update fields
    for key, value in profile_data.dict(exclude_unset=True).items():
        setattr(student, key, value)
    
    student.updated_by = current_user.id
    db.commit()
    db.refresh(student)
    
    return StudentProfileResponse.model_validate(student)

# ============================================================
# STUDENT CLASSES
# ============================================================

@router.get("/classes", response_model=List[StudentClassResponse])
async def get_student_classes(
    academic_sessions_id: Optional[int] = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Get student's class enrollments.
    """
    student = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    query = db.query(StudentClass).filter(
        StudentClass.student_id == student.student_id
    )
    
    if academic_sessions_id:
        query = query.filter(StudentClass.academic_sessions_id == academic_sessions_id)
    
    classes = query.order_by(StudentClass.academic_sessions_id.desc()).all()
    return [StudentClassResponse.model_validate(c) for c in classes]

# ============================================================
# STUDENT ATTENDANCE
# ============================================================

@router.get("/attendance/summary", response_model=StudentAttendanceResponse)
async def get_attendance_summary(
    academic_sessions_id: int,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Get student's attendance summary.
    """
    from app.model import StudentAttendance
    
    student = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    student_class = db.query(StudentClass).filter(
        StudentClass.student_id == student.student_id,
        StudentClass.academic_sessions_id == academic_sessions_id
    ).first()
    
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session"
        )
    
    attendance = db.query(StudentAttendance).filter(
        StudentAttendance.student_class_id == student_class.id
    ).first()
    
    if not attendance:
        attendance = StudentAttendance(
            student_class_id=student_class.id,
            total_classes=0,
            present_classes=0,
            absent_classes=0,
            attendance_percentage=0.0
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
    
    return StudentAttendanceResponse.model_validate(attendance)

@router.get("/attendance/daily", response_model=List[dict])
async def get_daily_attendance(
    academic_sessions_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Get student's daily attendance records.
    """
    student = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    student_class = db.query(StudentClass).filter(
        StudentClass.student_id == student.student_id,
        StudentClass.academic_sessions_id == academic_sessions_id
    ).first()
    
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session"
        )
    
    query = db.query(DailyClassStudent).filter(
        DailyClassStudent.student_class_id == student_class.id
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
            "remarks": r.remarks
        }
        for r in records
    ]

# ============================================================
# STUDENT ASSIGNMENTS
# ============================================================

@router.get("/assignments", response_model=List[AssignmentResultResponse])
async def get_student_assignments(
    academic_sessions_id: int,
    subject_id: Optional[int] = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Get student's assignment results.
    """
    student = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    student_class = db.query(StudentClass).filter(
        StudentClass.student_id == student.student_id,
        StudentClass.academic_sessions_id == academic_sessions_id
    ).first()
    
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session"
        )
    
    query = db.query(AssignmentResult).filter(
        AssignmentResult.student_class_id == student_class.id
    )
    
    if subject_id:
        query = query.join(Assignment).filter(
            Assignment.class_subject_id == subject_id
        )
    
    results = query.order_by(AssignmentResult.created_at.desc()).all()
    return [AssignmentResultResponse.model_validate(r) for r in results]

# ============================================================
# STUDENT EXAMS
# ============================================================

@router.get("/exams", response_model=List[ExamResultResponse])
async def get_student_exams(
    academic_sessions_id: int,
    subject_id: Optional[int] = None,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Get student's exam results.
    """
    student = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    student_class = db.query(StudentClass).filter(
        StudentClass.student_id == student.student_id,
        StudentClass.academic_sessions_id == academic_sessions_id
    ).first()
    
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session"
        )
    
    query = db.query(ExamResult).filter(
        ExamResult.student_class_id == student_class.id
    )
    
    if subject_id:
        query = query.join(Exam).filter(
            Exam.class_subject_id == subject_id
        )
    
    results = query.order_by(ExamResult.created_at.desc()).all()
    return [ExamResultResponse.model_validate(r) for r in results]

# ============================================================
# STUDENT FEES
# ============================================================

@router.get("/fees", response_model=List[FeeResponse])
async def get_student_fees(
    academic_sessions_id: int,
    fee_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Get student's fee records.
    """
    student = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    student_class = db.query(StudentClass).filter(
        StudentClass.student_id == student.student_id,
        StudentClass.academic_sessions_id == academic_sessions_id
    ).first()
    
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session"
        )
    
    query = db.query(Fee).filter(
        Fee.student_class_id == student_class.id
    )
    
    if fee_status:
        query = query.filter(Fee.status == fee_status)
    
    fees = query.order_by(Fee.fee_year.desc(), Fee.fee_month.desc()).all()
    return [FeeResponse.model_validate(f) for f in fees]

@router.get("/fees/summary")
async def get_fee_summary(
    academic_sessions_id: int,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db)
):
    """
    Get student's fee summary.
    """
    from decimal import Decimal
    
    student = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    student_class = db.query(StudentClass).filter(
        StudentClass.student_id == student.student_id,
        StudentClass.academic_sessions_id == academic_sessions_id
    ).first()
    
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session"
        )
    
    fees = db.query(Fee).filter(
        Fee.student_class_id == student_class.id
    ).all()
    
    total_amount = sum(f.total_amount for f in fees)
    paid_amount = sum(f.paid_amount for f in fees)
    pending_amount = total_amount - paid_amount
    
    return {
        "total_amount": float(total_amount),
        "paid_amount": float(paid_amount),
        "pending_amount": float(pending_amount),
        "status": "Paid" if pending_amount == 0 else "Pending"
    }
