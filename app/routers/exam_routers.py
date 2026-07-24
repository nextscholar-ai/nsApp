# from fastapi import APIRouter
# from fastapi import Depends
# from fastapi import HTTPException

# from sqlalchemy.orm import Session
# from sqlalchemy import func

# from app.model import (
#     StudentProfile,
#     Exam,
#     ExamResult,
#     Subject,
# )


# from app.schemas import (
#     ExamCreate,
#     ExamUpdate,
#     ExamResponse,
# )

# from app.dependencies import (
#     get_db,
#     get_current_student,
# )


# router = APIRouter(
#     prefix="/exams",
#     tags=["Exams"]
# )


# # =====================================================
# # CREATE EXAM RESULT
# # Teacher/Admin Use
# # =====================================================

# @router.post(
#     "/{student_id}",
#     response_model=ExamResponse
# )
# def create_exam(

#     student_id: str,

#     data: ExamCreate,

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

#     percentage: float = 0.0

#     # Ensure numeric types for DB model (ExamResult fields are Float)
#     total_marks = float(data.total_marks or 0)
#     obtained_marks = float(data.obtained_marks or 0)

#     if total_marks > 0:
#         percentage = round((obtained_marks / total_marks) * 100, 2)

#     # Resolve Exam row first so ExamResult can be linked via Exam_id
#     if data.exam_id is not None:
#         exam = db.query(Exam).filter(Exam.id == data.exam_id).first()
#         if not exam:
#             raise HTTPException(status_code=404, detail="Exam table row not found")
#     else:
#         exam = (
#             db.query(Exam)
#             .join(Subject, Exam.subject_id == Subject.id)
#             .filter(
#                 func.lower(Subject.subject_name) == data.subject_name.strip().lower(),
#                 Exam.exam_name == data.exam_name,
#                 Exam.exam_date == data.exam_date,
#             )
#             .first()
#         )


#         if not exam:
#             # Exam table model uses subject_id (not subject_name)
#             subject = (
#                 db.query(Subject)
#                 .filter(Subject.subject_name == data.subject_name)
#                 .first()
#             )
#             if not subject:
#                 raise HTTPException(status_code=404, detail="Subject not found")

#             exam = Exam(
#                 subject_id=subject.id,
#                 exam_name=data.exam_name,
#                 exam_date=data.exam_date,
#                 # These fields are required in model; set safe defaults
#                 duration="",
#                 title=None,
#                 total_marks=float(data.total_marks or 0),
#             )
#             db.add(exam)
#             db.commit()
#             db.refresh(exam)


#     # Exam model stores only subject_id; ExamResult expects subject_name
#     subject_for_result = (
#         db.query(Subject)
#         .filter(Subject.id == exam.subject_id)
#         .first()
#     )
#     if not subject_for_result:
#         raise HTTPException(status_code=404, detail="Subject not found")

#     result = ExamResult(
#         Exam_id=exam.id,
#         student_id=student.student_id,

#         subject_name=subject_for_result.subject_name.strip().title(),
#         exam_name=exam.exam_name,
#         exam_date=exam.exam_date,
#         total_marks=total_marks,
#         obtained_marks=obtained_marks,
#         percentage=percentage,
#     )


#     db.add(result)
#     db.commit()
#     db.refresh(result)

#     return result


# # =====================================================
# # UPDATE EXAM
# # =====================================================

# @router.put(
#     "/{exam_id}",
#     response_model=ExamResponse
# )
# def update_exam(

#     exam_id: str,

#     data: ExamUpdate,

#     db: Session = Depends(get_db)

# ):

#     exam = (
#         db.query(ExamResult)
#         .filter(
#             ExamResult.Exam_id == exam_id
#         )
#         .first()
#     )


#     if not exam:

#         raise HTTPException(
#             status_code=404,
#             detail="Exam not found"
#         )

#     update_data = data.model_dump(
#         exclude_unset=True
#     )

#     for field, value in update_data.items():

#         setattr(
#             exam,
#             field,
#             value
#         )

#     if exam.total_marks > 0:

#         exam.percentage = round(
#             (
#                 exam.obtained_marks
#                 /
#                 exam.total_marks
#             ) * 100,
#             2
#         )

#     db.commit()

#     db.refresh(exam)

#     return exam


# # =====================================================
# # STUDENT VIEW ALL EXAMS
# # =====================================================

# @router.get(
#     "/my-results",
#     response_model=list[ExamResponse]
# )
# def my_results(

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     return (

#         db.query(ExamResult)

#         .filter(
#             ExamResult.student_id
#             == student.student_id
#         )

#         .order_by(
#             ExamResult.exam_date.desc()
#         )

#         .all()
#     )


# # =====================================================
# # SINGLE RESULT
# # =====================================================

# @router.get(
#     "/result/{exam_id}",
#     response_model=ExamResponse
# )
# def single_result(

#     exam_id: str,

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     exam = (
#         db.query(ExamResult)
#         .filter(
#             ExamResult.Exam_id == exam_id,
#             ExamResult.student_id == student.student_id,
#         )
#         .first()
#     )

#     if not exam:

#         raise HTTPException(
#             status_code=404,
#             detail="Result not found"
#         )

#     return exam


# # =====================================================
# # FILTER BY SUBJECT
# # =====================================================

# @router.get(
#     "/subject/{subject_name}",
#     response_model=list[ExamResponse]
# )
# def results_by_subject(

#     subject_name: str,

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     return (

#         db.query(ExamResult)

#         .filter(
#             ExamResult.student_id
#             == student.student_id,

#             func.lower(Subject.subject_name)
#             == subject_name.strip().lower()
#         )

#         .all()
#     )


# ============================================================
# routers/exam_routers.py - Exam Routes
# ============================================================

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import ExamStatus, UserRole
from app.dependencies import get_current_user, require_role
from app.model import Exam, ExamResult, TeacherProfile, TeacherSubject, User
from app.schemas import (
    ExamCreate,
    ExamResponse,
    ExamResultCreate,
    ExamResultResponse,
    ExamUpdate,
)

router = APIRouter(prefix="/exams", tags=["Exams"])

# ============================================================
# EXAM CRUD
# ============================================================


@router.post("/", response_model=ExamResponse)
async def create_exam(
    exam_data: ExamCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new exam."""
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
            TeacherSubject.id == exam_data.teacher_subject_id,
            TeacherSubject.teacher_id == teacher.teacher_id,
        )
        .first()
    )

    if not teacher_subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class",
        )

    new_exam = Exam(
        exam_id=exam_data.exam_id,
        academic_sessions_id=exam_data.academic_sessions_id,
        classroom_id=exam_data.classroom_id,
        class_subject_id=exam_data.class_subject_id,
        teacher_subject_id=exam_data.teacher_subject_id,
        exam_name=exam_data.exam_name,
        exam_type=exam_data.exam_type,
        description=exam_data.description,
        exam_date=exam_data.exam_date,
        start_time=exam_data.start_time,
        end_time=exam_data.end_time,
        duration_minutes=exam_data.duration_minutes,
        room_number=exam_data.room_number,
        total_marks=exam_data.total_marks,
        passing_marks=exam_data.passing_marks,
        status=exam_data.status,
        publish_at=exam_data.publish_at,
        completed_at=exam_data.completed_at,
        created_by=current_user.id,
    )

    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)

    return ExamResponse.model_validate(new_exam)


@router.get("/", response_model=list[ExamResponse])
async def get_exams(
    classroom_id: str | None = None,
    status: ExamStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get exams with filters."""
    query = db.query(Exam)

    if classroom_id:
        query = query.filter(Exam.classroom_id == classroom_id)

    if status:
        query = query.filter(Exam.status == status)

    # For teachers, only show their exams
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
            query = query.filter(Exam.teacher_subject_id.in_(teacher_subject_ids))

    exams = query.order_by(Exam.exam_date.desc()).all()
    return [ExamResponse.model_validate(e) for e in exams]


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get exam by ID."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    return ExamResponse.model_validate(exam)


@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: str,
    exam_data: ExamUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Update exam."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    # Check ownership
    if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own exams",
        )

    for key, value in exam_data.model_dump(exclude_unset=True).items():
        setattr(exam, key, value)

    exam.updated_by = current_user.id
    db.commit()
    db.refresh(exam)

    return ExamResponse.model_validate(exam)


@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete exam."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    # Check ownership
    if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own exams",
        )

    exam.is_active = False
    exam.deleted_by = current_user.id
    db.commit()

    return {"success": True, "message": "Exam deleted successfully"}


# ============================================================
# EXAM RESULTS
# ============================================================


@router.post("/{exam_id}/results", response_model=list[ExamResultResponse])
async def upload_exam_results(
    exam_id: str,
    results_data: list[ExamResultCreate],
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Upload results for an exam."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    # Check ownership
    if exam.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload results for your own exams",
        )

    uploaded = []
    for item in results_data:
        # Create or update result
        existing = (
            db.query(ExamResult)
            .filter(
                ExamResult.exam_id == exam_id,
                ExamResult.student_class_id == item.student_class_id,
            )
            .first()
        )

        if existing:
            existing.obtained_marks = item.obtained_marks
            existing.percentage = item.percentage
            existing.grade = item.grade
            existing.remarks = item.remarks
            existing.rank_in_class = item.rank_in_class
            existing.is_absent = item.is_absent
            existing.checked_at = datetime.now(UTC)
            existing.checked_by = current_user.id
            uploaded.append(existing)
        else:
            new_result = ExamResult(
                exam_id=exam_id,
                student_class_id=item.student_class_id,
                obtained_marks=item.obtained_marks,
                percentage=item.percentage,
                grade=item.grade,
                remarks=item.remarks,
                rank_in_class=item.rank_in_class,
                is_absent=item.is_absent,
                checked_at=datetime.now(UTC),
                checked_by=current_user.id,
            )
            db.add(new_result)
            uploaded.append(new_result)

    # Update result count
    exam.result_uploaded = len(uploaded)

    db.commit()

    return [ExamResultResponse.model_validate(r) for r in uploaded]


@router.get("/{exam_id}/results", response_model=list[ExamResultResponse])
async def get_exam_results(
    exam_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get results for an exam."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )

    results = (
        db.query(ExamResult)
        .filter(ExamResult.exam_id == exam_id)
        .order_by(ExamResult.rank_in_class)
        .all()
    )

    return [ExamResultResponse.model_validate(r) for r in results]
