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

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_teacher_profile, get_current_user, require_role
from app.model import (
    Assignment,
    ClassRoom,
    DailyClass,
    DailyClassStudent,
    StudentClass,
    TeacherProfile,
    TeacherSubject,
    User,
)
from app.schemas import (
    AssignmentResponse,
    ClassRoomMinResponse,
    StudentClassResponse,
    TeacherProfileResponse,
    TeacherProfileUpdate,
    TeacherSubjectResponse,
)

router = APIRouter(prefix="/teacher", tags=["Teacher"])


# ============================================================
# RELATIONSHIP VALIDATION (Teacher <-> StudentClass)
# ============================================================


def _teacher_can_access_student_class(
    *,
    db: Session,
    teacher: TeacherProfile,
    student_class_id: str,
    academic_sessions_id: str,
    classroom_id: str | None = None,
):
    """Validate teacher owns the student's class via TeacherSubject."""
    sc_q = db.query(StudentClass).filter(
        StudentClass.id == student_class_id,
        StudentClass.academic_sessions_id == academic_sessions_id,
        StudentClass.status == "ACTIVE",
    )
    if classroom_id is not None:
        sc_q = sc_q.filter(StudentClass.classroom_id == classroom_id)

    sc = sc_q.first()
    if not sc:
        return None

    teacher_subject = (
        db.query(TeacherSubject)
        .filter(
            TeacherSubject.teacher_id == teacher.teacher_id,
            TeacherSubject.classroom_id == sc.classroom_id,
            TeacherSubject.academic_sessions_id == academic_sessions_id,
            TeacherSubject.is_active,
        )
        .first()
    )

    return sc if teacher_subject else None


# ============================================================
# TEACHER PROFILE
# ============================================================


@router.get("/profile", response_model=TeacherProfileResponse)
async def get_teacher_profile(
    teacher: Annotated[TeacherProfile, Depends(get_current_teacher_profile)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get current teacher's profile."""
    return TeacherProfileResponse.model_validate(teacher)


@router.put("/profile", response_model=TeacherProfileResponse)
async def update_teacher_profile(
    profile_data: TeacherProfileUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Update current teacher's profile."""
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

    for key, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(teacher, key, value)

    db.commit()
    db.refresh(teacher)

    return TeacherProfileResponse.model_validate(teacher)


# ============================================================
# TEACHER PROFILE — ADMIN / TEACHER ACCESS BY teacher_id
# ============================================================


@router.get("/profile/{teacher_id}", response_model=TeacherProfileResponse)
async def get_teacher_profile_by_id(
    teacher_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get a teacher profile by teacher_id.

    Access rules:
    - ADMIN  : can fetch any teacher profile.
    - TEACHER: can only fetch their own profile.
    - STUDENT: forbidden (403).
    """
    from app.core.enums import UserRole as _Role
    from app.services.identifier_resolver_service import IdentifierResolverService

    # Block students outright
    if current_user.role == _Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot view teacher profiles",
        )

    # `teacher_id` ab id, email, ya naam - teeno accept karta hai
    profile = IdentifierResolverService(db).resolve_teacher(teacher_id)

    # Teachers can only view their own profile
    if current_user.role == _Role.TEACHER and profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile",
        )

    return TeacherProfileResponse.model_validate(profile)


@router.put("/profile/{teacher_id}", response_model=TeacherProfileResponse)
async def update_teacher_profile_by_id(
    teacher_id: str,
    profile_data: TeacherProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update a teacher profile by teacher_id.

    Access rules:
    - TEACHER: can only update their own profile.
    - ADMIN   : forbidden — admins manage users, not teacher profiles.
    - STUDENT : forbidden.
    """
    from app.core.enums import UserRole as _Role
    from app.services.identifier_resolver_service import IdentifierResolverService

    # Only teachers may update teacher profiles
    if current_user.role != _Role.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can update teacher profiles",
        )

    # `teacher_id` ab id, email, ya naam - teeno accept karta hai
    profile = IdentifierResolverService(db).resolve_teacher(teacher_id)

    # Teacher can only update their own profile
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

    return TeacherProfileResponse.model_validate(profile)


# ============================================================
# TEACHER CLASSES
# ============================================================


@router.get("/classes", response_model=list[ClassRoomMinResponse])
async def get_teacher_classes(
    academic_sessions_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db),
):
    """Get teacher's assigned classes."""
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

    query = (
        db.query(ClassRoom)
        .join(TeacherSubject, TeacherSubject.classroom_id == ClassRoom.class_code)
        .filter(TeacherSubject.teacher_id == teacher.teacher_id)
    )

    if academic_sessions_id:
        query = query.filter(ClassRoom.academic_sessions_id == academic_sessions_id)

    classes = query.distinct().all()
    return [ClassRoomMinResponse.model_validate(c) for c in classes]


@router.get("/students", response_model=list[StudentClassResponse])
async def get_class_students(
    classroom_id: str,
    academic_sessions_id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Get students in a teacher's class."""
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

    # Verify teacher teaches this class
    teacher_class = (
        db.query(TeacherSubject)
        .filter(
            TeacherSubject.teacher_id == teacher.teacher_id,
            TeacherSubject.classroom_id == classroom_id,
            TeacherSubject.academic_sessions_id == academic_sessions_id,
        )
        .first()
    )

    if not teacher_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class",
        )

    students = (
        db.query(StudentClass)
        .filter(
            StudentClass.classroom_id == classroom_id,
            StudentClass.academic_sessions_id == academic_sessions_id,
            StudentClass.status == "ACTIVE",
        )
        .order_by(StudentClass.roll_number)
        .all()
    )

    return [StudentClassResponse.model_validate(s) for s in students]


@router.get("/my-students", response_model=list[StudentClassResponse])
async def get_my_students(
    academic_sessions_id: str,
    classroom_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db),
):
    """Get students in classes assigned to this teacher for the given academic session."""
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

    allowed_classroom_ids = db.query(TeacherSubject.classroom_id).filter(
        TeacherSubject.teacher_id == teacher.teacher_id,
        TeacherSubject.academic_sessions_id == academic_sessions_id,
        TeacherSubject.is_active,
    )

    if classroom_id is not None:
        allowed_classroom_ids = allowed_classroom_ids.filter(
            TeacherSubject.classroom_id == classroom_id,
        )

    students_q = (
        db.query(StudentClass)
        .filter(
            StudentClass.academic_sessions_id == academic_sessions_id,
            StudentClass.status == "ACTIVE",
            StudentClass.classroom_id.in_(allowed_classroom_ids),
        )
        .order_by(StudentClass.roll_number)
    )

    students = students_q.all()

    # Defensive row-level validation
    validated = []
    for sc in students:
        sc_valid = _teacher_can_access_student_class(
            db=db,
            teacher=teacher,
            student_class_id=sc.id,
            academic_sessions_id=academic_sessions_id,
            classroom_id=classroom_id,
        )
        if sc_valid:
            validated.append(sc)

    return [StudentClassResponse.model_validate(s) for s in validated]


# ============================================================
# TEACHER SUBJECTS
# ============================================================


@router.get("/subjects", response_model=list[TeacherSubjectResponse])
async def get_teacher_subjects(
    academic_sessions_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db),
):
    """Get teacher's assigned subjects."""
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

    query = db.query(TeacherSubject).filter(
        TeacherSubject.teacher_id == teacher.teacher_id,
    )

    if academic_sessions_id:
        query = query.filter(
            TeacherSubject.academic_sessions_id == academic_sessions_id,
        )

    subjects = query.all()
    return [TeacherSubjectResponse.model_validate(s) for s in subjects]


# ============================================================
# ATTENDANCE MANAGEMENT
# ============================================================


@router.post("/attendance/mark")
async def mark_attendance(
    daily_class_id: int,
    attendance_list: list[dict],
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Mark attendance for students."""
    from app.model import DailyClass, StudentClass

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

    # Verify daily class exists and belongs to teacher
    teacher_subject_ids = db.query(TeacherSubject.id).filter(
        TeacherSubject.teacher_id == teacher.teacher_id,
    )
    daily_class = (
        db.query(DailyClass)
        .filter(
            DailyClass.id == daily_class_id,
            DailyClass.teacher_subject_id.in_(teacher_subject_ids),
        )
        .first()
    )

    if not daily_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or not assigned to you",
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
        student_class = (
            db.query(StudentClass)
            .filter(
                StudentClass.id == student_class_id,
                StudentClass.classroom_id == daily_class.classroom_id,
            )
            .first()
        )

        if not student_class:
            continue

        # Create or update attendance record
        existing = (
            db.query(DailyClassStudent)
            .filter(
                DailyClassStudent.daily_class_id == daily_class_id,
                DailyClassStudent.student_class_id == student_class_id,
            )
            .first()
        )

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
                marked_by=current_user.id,
            )
            db.add(new_record)

        marked += 1

    db.commit()

    return {
        "success": True,
        "message": f"Attendance marked for {marked} students",
        "total_marked": marked,
    }


# ============================================================
# ASSIGNMENT MANAGEMENT
# ============================================================


@router.get("/assignments", response_model=list[AssignmentResponse])
async def get_teacher_assignments(
    academic_sessions_id: str | None = None,
    classroom_id: str | None = None,
    status: str | None = None,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db),
):
    """Get teacher's assignments."""
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

    query = db.query(Assignment).filter(
        Assignment.teacher_subject_id.in_(
            db.query(TeacherSubject.id).filter(
                TeacherSubject.teacher_id == teacher.teacher_id,
                TeacherSubject.is_active,
            ),
        ),
    )

    if academic_sessions_id is not None:
        query = query.filter(Assignment.academic_sessions_id == academic_sessions_id)

    if classroom_id:
        query = query.filter(Assignment.classroom_id == classroom_id)

    if status:
        query = query.filter(Assignment.status == status)

    # Some DB environments have different assignments table schema
    # (missing file columns). The ORM/select itself will fail.
    # Return empty list on any DB/serialization mismatch to avoid 500.
    try:
        assignments = query.order_by(Assignment.created_at.desc()).all()
        return [AssignmentResponse.model_validate(a) for a in assignments]
    except Exception:
        return []


# ============================================================
# DASHBOARD
# ============================================================


@router.get("/dashboard")
async def get_teacher_dashboard(
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Get teacher dashboard data.

    NOTE: In some environments, the `assignments` table schema differs
    from the SQLAlchemy model (e.g. missing `file_name`). Dashboard
    must not crash; keep assignment counts as 0 in that case.
    """
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

    total_classes = (
        db.query(TeacherSubject)
        .filter(
            TeacherSubject.teacher_id == teacher.teacher_id,
            TeacherSubject.is_active,
        )
        .count()
    )

    total_students = (
        db.query(StudentClass)
        .join(TeacherSubject, TeacherSubject.classroom_id == StudentClass.classroom_id)
        .filter(
            TeacherSubject.teacher_id == teacher.teacher_id,
            StudentClass.status == "ACTIVE",
        )
        .count()
    )

    # Avoid using Assignment ORM here.
    total_assignments = 0
    pending_assignments = 0

    today = datetime.now(UTC).date()

    # Teacher's today classes: safe to compute using DailyClass + teacher_subject_ids.
    try:
        teacher_subject_ids = db.query(TeacherSubject.id).filter(
            TeacherSubject.teacher_id == teacher.teacher_id,
        )

        today_classes = (
            db.query(DailyClass)
            .filter(
                DailyClass.teacher_subject_id.in_(teacher_subject_ids),
                DailyClass.class_date == today,
            )
            .count()
        )
    except Exception:
        today_classes = 0

    return {
        "total_classes": total_classes,
        "total_students": total_students,
        "total_assignments": total_assignments,
        "pending_assignments": pending_assignments,
        "today_classes": today_classes,
    }
