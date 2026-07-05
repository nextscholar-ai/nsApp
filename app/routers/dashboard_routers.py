# from fastapi import APIRouter
# from fastapi import Depends

# from sqlalchemy.orm import Session
# from sqlalchemy import func

# from app.dependencies import (
#     get_db,
#     get_current_student,
#     require_role
# )

# from app.model import (
#     StudentProfile,
#     AlumnusDetail,
#     SubjectProgress,
#     DailyClass,
#     Assignment,
#     AssignmentSubmission,
#     ExamResult,
#     Fee,
#     ChatMessage
# )
# from app.schemas import StudentDashboardSchema


# router = APIRouter(
#     prefix="/dashboard",
#     tags=["Dashboard"]
# )


# # =====================================================
# # STUDENT DASHBOARD SUMMARY
# # =====================================================

# @router.get("/student",response_model=StudentDashboardSchema)
# def dashboard(

#     current_user = Depends(
#         require_role("student")
#     ),

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(
#         get_db
#     )
# ):

#     alumnus = (

#         db.query(AlumnusDetail)

#         .filter(
# AlumnusDetail.student_id
#             == student.student_id
#         )

#         .first()
#     )

#     progress_count = (

#         db.query(
#             SubjectProgress
#         )

#         .filter(
#             SubjectProgress.student_id
#             == student.student_id
#         )

#         .count()
#     )

#     total_classes = (

#         db.query(
#             DailyClass
#         )

#         .filter(
#             DailyClass.student_id
#             == student.student_id
#         )

#         .count()
#     )

#     present_classes = (

#         db.query(
#             DailyClass
#         )

#         .filter(
#             DailyClass.student_id
#             == student.student_id,

#             func.lower(DailyClass.attendance).in_(["p", "present"])
#         )

#         .count()
#     )

#     assignments = (

#         db.query(
#             AssignmentSubmission
#         )

#         .filter(
#             AssignmentSubmission.student_id
#             == student.student_id
#         )

#         .count()
#     )


#     exams = (

#         db.query(
#             ExamResult
#         )

#         .filter(
#             ExamResult.student_id
#             == student.student_id
#         )

#         .count()
#     )

#     avg_percentage = (

#         db.query(
#             func.avg(
#                 ExamResult.percentage
#             )
#         )

#         .filter(
#             ExamResult.student_id
#             == student.student_id
#         )

#         .scalar()
#     )

#     paid_count = (
#         db.query(Fee)
#         .filter(
#             Fee.student_id == student.student_id,
#             func.lower(Fee.status) == "paid"
#         )
#         .count()
#     )

#     remaining_count = (
#         db.query(Fee)
#         .filter(
#             Fee.student_id == student.student_id,
#             func.lower(Fee.status) == "remaining"
#         )
#         .count()
#     )

#     total_messages = (

#         db.query(
#             ChatMessage
#         )

#         .filter(
#             ChatMessage.student_id
#             == student.student_id
#         )

#         .count()
#     )

#     recent_classes = (
#         db.query(DailyClass)
#         .filter(
#             DailyClass.student_id
#             == student.student_id
#         )
#         .order_by(
#             DailyClass.class_date.desc()
#         )
#         .limit(10)
#         .all()
#     )

#     class_data = [
#         {
#             "subject_name": cls.subject_name,
#             "teacher_name": cls.teacher_name,
#             "day_name": cls.day_name,
#             "attendance": cls.attendance,
#             "class_date": cls.class_date
#         }
#         for cls in recent_classes
#     ]
#     attendance_percentage = 0

#     if total_classes > 0:

#         attendance_percentage = round(

#             (
#                 present_classes
#                 /
#                 total_classes
#             ) * 100,

#             2
#         )

#     return {

#         # ==========================
#         # PROFILE
#         # ==========================

#         "student_profile": {

#             "student_id":
#             student.student_id,

#             "student_name":
#             student.student_name,

#             "student_email":
#             student.student_email,

#             "student_phone":
#             student.student_phone,

#             "student_class":
#             student.student_class,

#             "school_name":
#             student.school_name,

#             "school_address":
#             student.school_address,

#             "parent_name":
#             student.parent_name,

#             "parent_phone":
#             student.parent_phone,

#             "guardian_name":
#             student.guardian_name,

#             "guardian_phone":
#             student.guardian_phone,

#             "medium":
#             student.medium,

#             "board":
#             student.board
#         },

#         # ==========================
#         # ALUMNUS
#         # ==========================

#         "alumnus_available":
#         alumnus is not None,

#         # ==========================
#         # SUBJECT
#         # ==========================

#         "subject_progress_count":
#         progress_count,

#         # ==========================
#         # ATTENDANCE
#         # ==========================

#         "attendance": {

#             "total_classes":
#             total_classes,

#             "present_classes":
#             present_classes,

#             "attendance_percentage":
#             attendance_percentage
#         },

#         # ==========================
#         # ASSIGNMENT
#         # ==========================

#         "assignments": {

#             "total_assignments":
#             assignments
#         },

#         # ==========================
#         # EXAM
#         # ==========================

#         "exam_summary": {

#             "total_exams":
#             exams,

#             "average_percentage":
#             round(
#                 avg_percentage or 0,
#                 2
#             )
#         },

#         # ==========================
#         # FEES
#         # ==========================

#         "fees": {

#             "paid_months":
#             paid_count,

#             "remaining_months":
#             remaining_count
#         },

#         # ==========================
#         # CHAT
#         # ==========================

#         "chat": {

#             "total_messages":
#             total_messages
#         },

#         # ==========================
#         # RECENT CLASSES
#         # ==========================

#         "recent_classes":
#         class_data
#     }

# ============================================================
# routers/dashboard_routers.py - Dashboard Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Dict, Any

from app.api.database import get_db
from app.model import (
    User, StudentProfile, TeacherProfile, AdminProfile,
    ClassRoom, Subject, StudentClass, DailyClass,
    Assignment, Exam, Fee, Notice
)
from app.dependencies import (
    get_current_user,
    get_current_student_profile,
    get_current_teacher_profile,
    require_role
)
from app.core.enums import UserRole, AssignmentStatus, ExamStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# ============================================================
# STUDENT DASHBOARD
# ============================================================

@router.get("/student")
async def get_student_dashboard(
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db)
):
    """
    Get student dashboard data.
    """
    # Get current session
    from app.model import AcademicSession
    current_session = db.query(AcademicSession).filter(
        AcademicSession.is_current == True
    ).first()
    
    if not current_session:
        return {"error": "No current academic session found"}
    
    # Get student class
    student_class = db.query(StudentClass).filter(
        StudentClass.student_id == student.student_id,
        StudentClass.academic_sessions_id == current_session.id
    ).first()
    
    if not student_class:
        return {"error": "Student not enrolled in current session"}
    
    # Get attendance summary
    from app.model import StudentAttendance
    attendance = db.query(StudentAttendance).filter(
        StudentAttendance.student_class_id == student_class.id
    ).first()
    
    # Get upcoming assignments
    from app.model import Assignment
    upcoming_assignments = db.query(Assignment).filter(
        Assignment.classroom_id == student_class.classroom_id,
        Assignment.due_date >= date.today(),
        Assignment.status.in_([AssignmentStatus.PUBLISHED, AssignmentStatus.DRAFT])
    ).order_by(Assignment.due_date).limit(5).all()
    
    # Get upcoming exams
    from app.model import Exam
    upcoming_exams = db.query(Exam).filter(
        Exam.classroom_id == student_class.classroom_id,
        Exam.exam_date >= date.today(),
        Exam.status.in_([ExamStatus.PUBLISHED, ExamStatus.DRAFT])
    ).order_by(Exam.exam_date).limit(5).all()
    
    # Get fee status
    from app.model import Fee
    fees = db.query(Fee).filter(
        Fee.student_class_id == student_class.id
    ).all()
    
    total_fee = sum(f.total_amount for f in fees)
    paid_fee = sum(f.paid_amount for f in fees)
    
    return {
        "student": {
            "name": student.student_name,
            "student_id": student.student_id,
            "class": student_class.classroom.display_name if student_class.classroom else "",
            "roll_number": student_class.roll_number
        },
        "attendance": {
            "total_classes": attendance.total_classes if attendance else 0,
            "present": attendance.present_classes if attendance else 0,
            "percentage": attendance.attendance_percentage if attendance else 0
        },
        "upcoming_assignments": [
            {
                "id": a.id,
                "title": a.title,
                "due_date": a.due_date,
                "status": a.status
            }
            for a in upcoming_assignments
        ],
        "upcoming_exams": [
            {
                "id": e.id,
                "exam_name": e.exam_name,
                "exam_date": e.exam_date,
                "status": e.status
            }
            for e in upcoming_exams
        ],
        "fees": {
            "total": float(total_fee),
            "paid": float(paid_fee),
            "pending": float(total_fee - paid_fee)
        }
    }

# ============================================================
# TEACHER DASHBOARD
# ============================================================

@router.get("/teacher")
async def get_teacher_dashboard(
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db)
):
    """
    Get teacher dashboard data.
    """
    # Get current session
    from app.model import AcademicSession
    current_session = db.query(AcademicSession).filter(
        AcademicSession.is_current == True
    ).first()
    
    if not current_session:
        return {"error": "No current academic session found"}
    
    # Get teacher subjects
    from app.model import TeacherSubject
    teacher_subjects = db.query(TeacherSubject).filter(
        TeacherSubject.teacher_id == teacher.teacher_id,
        TeacherSubject.academic_sessions_id == current_session.id
    ).all()
    
    class_ids = [ts.classroom_id for ts in teacher_subjects]
    teacher_subject_ids = [ts.id for ts in teacher_subjects]

    # Get today's classes
    today = date.today()
    today_classes = db.query(DailyClass).filter(
        DailyClass.teacher_subject_id.in_(teacher_subject_ids),
        DailyClass.class_date == today
    ).count()
    
    # Get total students
    from app.model import StudentClass
    total_students = db.query(StudentClass).filter(
        StudentClass.classroom_id.in_(class_ids),
        StudentClass.academic_sessions_id == current_session.id,
        StudentClass.status == "ACTIVE"
    ).count()
    
    # Get pending assignments
    from app.model import Assignment
    pending_assignments = db.query(Assignment).filter(
        Assignment.teacher_subject_id.in_(teacher_subject_ids),
        Assignment.status == AssignmentStatus.DRAFT
    ).count()
    
    # Get upcoming exams
    from app.model import Exam
    upcoming_exams = db.query(Exam).filter(
        Exam.teacher_subject_id.in_(teacher_subject_ids),
        Exam.exam_date >= date.today(),
        Exam.status.in_([ExamStatus.PUBLISHED, ExamStatus.DRAFT])
    ).count()
    
    return {
        "teacher": {
            "name": teacher.teacher_name,
            "teacher_id": teacher.teacher_id,
            "designation": teacher.designation
        },
        "summary": {
            "total_classes": len(class_ids),
            "total_students": total_students,
            "today_classes": today_classes,
            "pending_assignments": pending_assignments,
            "upcoming_exams": upcoming_exams
        },
        "recent_activity": {
            "last_7_days_classes": db.query(DailyClass).filter(
                DailyClass.teacher_subject_id.in_(teacher_subject_ids),
                DailyClass.class_date >= today - timedelta(days=7)
            ).count()
        }
    }

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get("/admin")
async def get_admin_dashboard(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get admin dashboard data.
    """
    # Get current session
    from app.model import AcademicSession
    current_session = db.query(AcademicSession).filter(
        AcademicSession.is_current == True
    ).first()
    
    # System-wide statistics
    total_user = db.query(User).filter(User.is_deleted == False).count()
    total_students = db.query(StudentProfile).filter(StudentProfile.is_active == True).count()
    total_teachers = db.query(TeacherProfile).filter(TeacherProfile.is_active == True).count()
    total_classes = db.query(ClassRoom).filter(ClassRoom.is_active == True).count()
    total_subjects = db.query(Subject).filter(Subject.is_active == True).count()
    
    # Current session statistics
    if current_session:
        session_classes = db.query(ClassRoom).filter(
            ClassRoom.academic_sessions_id == current_session.id
        ).count()
        session_students = db.query(StudentClass).filter(
            StudentClass.academic_sessions_id == current_session.id,
            StudentClass.status == "ACTIVE"
        ).count()
    else:
        session_classes = 0
        session_students = 0
    
    # Recent activity
    recent_user = db.query(User).order_by(
        User.created_at.desc()
    ).limit(5).all()
    
    recent_notices = db.query(Notice).order_by(
        Notice.created_at.desc()
    ).limit(5).all()
    
    return {
        "system": {
            "total_user": total_user,
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_classes": total_classes,
            "total_subjects": total_subjects
        },
        "current_session": {
            "session_name": current_session.session_name if current_session else "None",
            "total_classes": session_classes,
            "total_students": session_students
        },
        "recent_activity": {
            "recent_user": [
                {
                    "id": u.id,
                    "email": u.email,
                    "role": u.role,
                    "created_at": u.created_at
                }
                for u in recent_user
            ],
            "recent_notices": [
                {
                    "id": n.id,
                    "title": n.title,
                    "created_at": n.created_at
                }
                for n in recent_notices
            ]
        }
    }
