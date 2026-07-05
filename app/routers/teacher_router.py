# from fastapi import APIRouter
# from fastapi import Depends

# from app.dependencies import (
#     get_current_teacher
# )

# router = APIRouter(
#     prefix="/teacher",
#     tags=["Teacher"]
# )

# @router.get("/dashboard")
# def teacher_dashboard(
#     teacher=Depends(
#         get_current_teacher
#     )
# ):

#     return {

#         "teacher_id":
#         teacher.teacher_id,

#         "teacher_name":
#         teacher.teacher_name,

#         "role":
#         "teacher"
#     }



# ============================================================
# routers/teacher_router.py - Teacher Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.api.database import get_db
from app.model import User, TeacherProfile, TeacherSubject, ClassRoom, StudentClass, DailyClass, Assignment
from app.schemas import (
    TeacherProfileResponse,
    TeacherProfileUpdate,
    TeacherSubjectResponse,
    ClassRoomMinResponse,
    StudentClassResponse,
    DailyClassResponse,
    DailyClassCreate,
    AssignmentResponse,
    AssignmentCreate,
    ResponseSchema,
    PaginatedResponseSchema
)
from app.dependencies import (
    get_current_user,
    get_current_teacher_profile,
    require_role
)
from app.core.enums import UserRole, AssignmentStatus

router = APIRouter(prefix="/teacher", tags=["Teacher"])

# ============================================================
# TEACHER PROFILE
# ============================================================

@router.get("/profile", response_model=TeacherProfileResponse)
async def get_teacher_profile(
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db)
):
    """
    Get current teacher's profile.
    """
    return TeacherProfileResponse.model_validate(teacher)

@router.put("/profile", response_model=TeacherProfileResponse)
async def update_teacher_profile(
    profile_data: TeacherProfileUpdate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Update current teacher's profile.
    """
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    for key, value in profile_data.dict(exclude_unset=True).items():
        setattr(teacher, key, value)
    
    db.commit()
    db.refresh(teacher)
    
    return TeacherProfileResponse.model_validate(teacher)

# ============================================================
# TEACHER CLASSES
# ============================================================

@router.get("/classes", response_model=List[ClassRoomMinResponse])
async def get_teacher_classes(
    academic_sessions_id: Optional[int] = None,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Get teacher's assigned classes.
    """
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    query = db.query(ClassRoom).join(
        TeacherSubject,
        TeacherSubject.classroom_id == ClassRoom.id
    ).filter(
        TeacherSubject.teacher_id == teacher.teacher_id
    )
    
    if academic_sessions_id:
        query = query.filter(ClassRoom.academic_sessions_id == academic_sessions_id)
    
    classes = query.distinct().all()
    return [ClassRoomMinResponse.model_validate(c) for c in classes]

@router.get("/students", response_model=List[StudentClassResponse])
async def get_class_students(
    classroom_id: int,
    academic_sessions_id: int,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Get students in a teacher's class.
    """
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Verify teacher teaches this class
    teacher_class = db.query(TeacherSubject).filter(
        TeacherSubject.teacher_id == teacher.teacher_id,
        TeacherSubject.classroom_id == classroom_id,
        TeacherSubject.academic_sessions_id == academic_sessions_id
    ).first()
    
    if not teacher_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class"
        )
    
    students = db.query(StudentClass).filter(
        StudentClass.classroom_id == classroom_id,
        StudentClass.academic_sessions_id == academic_sessions_id,
        StudentClass.status == "ACTIVE"
    ).order_by(StudentClass.roll_number).all()
    
    return [StudentClassResponse.model_validate(s) for s in students]

# ============================================================
# TEACHER SUBJECTS
# ============================================================

@router.get("/subjects", response_model=List[TeacherSubjectResponse])
async def get_teacher_subjects(
    academic_sessions_id: Optional[int] = None,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Get teacher's assigned subjects.
    """
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    query = db.query(TeacherSubject).filter(
        TeacherSubject.teacher_id == teacher.teacher_id
    )
    
    if academic_sessions_id:
        query = query.filter(TeacherSubject.academic_sessions_id == academic_sessions_id)
    
    subjects = query.all()
    return [TeacherSubjectResponse.model_validate(s) for s in subjects]

# ============================================================
# ATTENDANCE MANAGEMENT
# ============================================================

@router.post("/attendance/mark")
async def mark_attendance(
    daily_class_id: int,
    attendance_list: List[dict],
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Mark attendance for students.
    """
    from app.model import DailyClass, DailyClassStudent, StudentClass
    
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Verify daily class exists and belongs to teacher
    teacher_subject_ids = db.query(TeacherSubject.id).filter(
        TeacherSubject.teacher_id == teacher.teacher_id
    )
    daily_class = db.query(DailyClass).filter(
        DailyClass.id == daily_class_id,
        DailyClass.teacher_subject_id.in_(teacher_subject_ids)
    ).first()
    
    if not daily_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or not assigned to you"
        )
    
    # Process attendance
    marked = 0
    for item in attendance_list:
        student_class_id = item.get("student_class_id")
        status_val = item.get("attendance_status", "Present")
        is_late = item.get("is_late", False)
        late_minutes = item.get("late_minutes", 0)
        remarks = item.get("remarks")
        
        # Check if student exists in this class
        student_class = db.query(StudentClass).filter(
            StudentClass.id == student_class_id,
            StudentClass.classroom_id == daily_class.classroom_id
        ).first()
        
        if not student_class:
            continue
        
        # Create or update attendance record
        existing = db.query(DailyClassStudent).filter(
            DailyClassStudent.daily_class_id == daily_class_id,
            DailyClassStudent.student_class_id == student_class_id
        ).first()
        
        if existing:
            existing.attendance_status = status_val
            existing.is_late = is_late
            existing.late_minutes = late_minutes
            existing.remarks = remarks
            existing.marked_by = current_user.id
        else:
            new_record = DailyClassStudent(
                daily_class_id=daily_class_id,
                student_class_id=student_class_id,
                attendance_status=status_val,
                is_late=is_late,
                late_minutes=late_minutes,
                remarks=remarks,
                marked_by=current_user.id
            )
            db.add(new_record)
        
        marked += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Attendance marked for {marked} students",
        "total_marked": marked
    }

# ============================================================
# ASSIGNMENT MANAGEMENT
# ============================================================

@router.get("/assignments", response_model=List[AssignmentResponse])
async def get_teacher_assignments(
    classroom_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Get teacher's assignments.
    """
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    query = db.query(Assignment).filter(
        Assignment.teacher_subject_id.in_(
            db.query(TeacherSubject.id).filter(
                TeacherSubject.teacher_id == teacher.teacher_id
            )
        )
    )
    
    if classroom_id:
        query = query.filter(Assignment.classroom_id == classroom_id)
    
    if status:
        query = query.filter(Assignment.status == status)
    
    assignments = query.order_by(Assignment.created_at.desc()).all()
    return [AssignmentResponse.model_validate(a) for a in assignments]

# ============================================================
# DASHBOARD
# ============================================================

@router.get("/dashboard")
async def get_teacher_dashboard(
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Get teacher dashboard data.
    """
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Get counts
    total_classes = db.query(TeacherSubject).filter(
        TeacherSubject.teacher_id == teacher.teacher_id,
        TeacherSubject.is_active == True
    ).count()
    
    total_students = db.query(StudentClass).join(
        TeacherSubject,
        TeacherSubject.classroom_id == StudentClass.classroom_id
    ).filter(
        TeacherSubject.teacher_id == teacher.teacher_id,
        StudentClass.status == "ACTIVE"
    ).count()

    teacher_subject_ids = db.query(TeacherSubject.id).filter(
        TeacherSubject.teacher_id == teacher.teacher_id
    )

    total_assignments = db.query(Assignment).filter(
        Assignment.teacher_subject_id.in_(teacher_subject_ids)
    ).count()
    
    pending_assignments = db.query(Assignment).filter(
        Assignment.teacher_subject_id.in_(teacher_subject_ids),
        Assignment.status == AssignmentStatus.DRAFT
    ).count()
    
    # Get today's classes
    today = date.today()
    today_classes = db.query(DailyClass).filter(
        DailyClass.teacher_subject_id.in_(teacher_subject_ids),
        DailyClass.class_date == today
    ).count()
    
    return {
        "total_classes": total_classes,
        "total_students": total_students,
        "total_assignments": total_assignments,
        "pending_assignments": pending_assignments,
        "today_classes": today_classes
    }
