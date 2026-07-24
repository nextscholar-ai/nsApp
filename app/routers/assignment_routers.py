# from fastapi import APIRouter
# from fastapi import Depends
# from fastapi import HTTPException
# from sqlalchemy import func

# from sqlalchemy.orm import Session

# from app.model import (
#     Assignment,
#     Subject,
#     User,
#     StudentProfile
# )


# from app.schemas import (
#     AssignmentCreate,
#     AssignmentResponse,
#     AssignmentUpdate
# )

# from app.dependencies import (
#     get_db,
#     get_current_student,
#     require_role,
#     verify_assignment_owner

# )

# router = APIRouter(
#     prefix="/assignments",
#     tags=["Assignments"]
# )


# # =====================================================
# # CREATE ASSIGNMENT
# # Teacher/Admin Use
# # =====================================================

# @router.post(
#     "/",
#     response_model=AssignmentResponse
# )
# def create_assignment(

#     data: AssignmentCreate,

#     current_user: User = Depends(
#         require_role(
#             "teacher",
#             "admin"
#         )
#     ),

#     db: Session = Depends(get_db)

# ):

#     subject = (

#         db.query(Subject)

#         .filter(
#             Subject.id
#             == data.subject_id
#         )

#         .first()
#     )

#     if not subject:

#         raise HTTPException(
#             status_code=404,
#             detail="Subject not found"
#         )

#     assignment = Assignment(

#         subject_id=data.subject_id,

#         title=data.title.strip(),

#         description=data.description,

#         due_date=data.due_date,

#         created_by_user_id=current_user.id
#     )

#     db.add(assignment)

#     db.commit()

#     db.refresh(assignment)

#     return assignment


# @router.put(
#     "/{assignment_id}",
#     response_model=AssignmentResponse
# )
# def update_assignment(

#     assignment_id: str,

#     data: AssignmentUpdate,

#     current_user: User = Depends(
#         require_role(
#             "teacher",
#             "admin"
#         )
#     ),

#     db: Session = Depends(get_db)

# ):

#     assignment = verify_assignment_owner(
#         assignment_id,
#         current_user,
#         db
#     )

#     if not assignment:

#         raise HTTPException(
#             status_code=404,
#             detail="Assignment not found"
#         )

#     update_data = data.model_dump(
#         exclude_unset=True
#     )

#     for key, value in update_data.items():


#         setattr(
#             assignment,
#             key,
#             value
#         )

#     assignment.updated_by_user_id = (
#         current_user.id
#     )

#     db.commit()

#     db.refresh(assignment)

#     return assignment


# @router.delete(
#     "/{assignment_id}"
# )
# def delete_assignment(

#     assignment_id: str,

#     current_user: User = Depends(
#         require_role(
#             "teacher",
#             "admin"
#         )
#     ),

#     db: Session = Depends(get_db)

# ):

#     assignment = verify_assignment_owner(
#         assignment_id,
#         current_user,
#         db
#     )

#     if not assignment:

#         raise HTTPException(
#             status_code=404,
#             detail="Assignment not found"
#         )

#     assignment.is_active = False

#     db.commit()

#     return {
#         "message":
#         "Assignment deleted successfully"
#     }


# @router.get(
#     "/all",
#     response_model=list[
#         AssignmentResponse
#     ]
# )
# def get_all_assignments(

#     current_user: User = Depends(
#         require_role(
#             "teacher",
#             "admin"
#         )
#     ),

#     db: Session = Depends(get_db)

# ):

#     return (

#         db.query(Assignment).filter(
#             Assignment.is_active == True
#         )

#         .order_by(
#             Assignment.due_date.desc()
#         )

#         .all()
#     )
# # =====================================================
# # STUDENT VIEW ASSIGNMENTS
# # =====================================================

# @router.get(
#     "/my-assignments",
#     response_model=list[AssignmentResponse]
# )
# def my_assignments(

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     # Assignment is global, so return all assignments ordered by due date
#     return (

#         db.query(Assignment)

#         .order_by(
#             Assignment.due_date.desc()
#         )

#         .all()
#     )


# # =====================================================
# # GET SINGLE ASSIGNMENT
# # =====================================================

# @router.get(
#     "/{assignment_id}",
#     response_model=AssignmentResponse
# )
# def get_assignment(

#     assignment_id: str,

#     db: Session = Depends(get_db)

# ):

#     assignment = (

#         db.query(Assignment)

#         .filter(
#             Assignment.id == assignment_id
#         )

#         .first()
#     )

#     if not assignment:

#         raise HTTPException(
#             status_code=404,
#             detail="Assignment not found"
#         )

#     return assignment


# # =====================================================
# # FILTER BY SUBJECT
# # =====================================================

# @router.get(
#     "/subject/{subject_name}",
#     response_model=list[AssignmentResponse]
# )
# def assignments_by_subject(

#     subject_name: str,

#     db: Session = Depends(get_db)

# ):

#     # Filter by subject name (Assignment stores subject_id)
#     return (

#         db.query(Assignment)

#         .join(
#             Subject,
#             Assignment.subject_id == Subject.id
#         )

#         .filter(
#            func.lower(Subject.subject_name)
#            == subject_name.strip().lower()


#         )

#         .all()
#     )


# ============================================================
# routers/assignment_routers.py - Assignment Routes
# ============================================================

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import AssignmentStatus, UserRole
from app.dependencies import get_current_user, require_role
from app.model import Assignment, AssignmentResult, TeacherProfile, TeacherSubject, User
from app.schemas import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentResultCreate,
    AssignmentResultResponse,
    AssignmentUpdate,
)

router = APIRouter(prefix="/assignments", tags=["Assignments"])

# ============================================================
# ASSIGNMENT CRUD
# ============================================================


@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new assignment."""
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
            TeacherSubject.id == assignment_data.teacher_subject_id,
            TeacherSubject.teacher_id == teacher.teacher_id,
        )
        .first()
    )

    if not teacher_subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class",
        )

    # Build kwargs, but only pass columns that actually exist on the SQLAlchemy
    # `Assignment` model. This prevents crashes when DB schema differs.
    assignment_kwargs = {
        "assignment_id": assignment_data.assignment_id,
        "academic_sessions_id": assignment_data.academic_sessions_id,
        "classroom_id": assignment_data.classroom_id,
        "class_subject_id": assignment_data.class_subject_id,
        "teacher_subject_id": assignment_data.teacher_subject_id,
        "title": assignment_data.title,
        "description": assignment_data.description,
        "instructions": assignment_data.instructions,
        "due_date": assignment_data.due_date,
        "due_time": assignment_data.due_time,
        "total_marks": assignment_data.total_marks,
        "passing_marks": assignment_data.passing_marks,
        "uploaded_by": current_user.id,
        "status": assignment_data.status,
        "publish_at": assignment_data.publish_at,
        "close_at": assignment_data.close_at,
        "created_by": current_user.id,
    }

    # Add file_* fields if present and non-null.
    for k in ("file_name", "file_path", "file_type", "file_size"):
        if hasattr(assignment_data, k):
            val = getattr(assignment_data, k)
            if val is not None:
                assignment_kwargs[k] = val

    # Map attachment/file fields to whatever the DB schema actually supports.
    # Your DB table uses attachment_name/attachment_url/attachment_size,
    # but the SQLAlchemy model uses file_name/file_path/file_type/file_size.
    if "file_name" in assignment_kwargs and "attachment_name" in {
        c.name for c in Assignment.__table__.columns
    }:
        assignment_kwargs["attachment_name"] = assignment_kwargs.pop("file_name")

    # Filter out keys not mapped on the SQLAlchemy model.
    mapped_columns = {c.name for c in Assignment.__table__.columns}
    filtered_kwargs = {
        k: v for k, v in assignment_kwargs.items() if k in mapped_columns
    }

    try:
        new_assignment = Assignment(**filtered_kwargs)

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to create assignment object: {type(exc).__name__}",
        ) from exc

    try:
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to create assignment in current DB schema: {type(exc).__name__}",
        ) from exc

    return AssignmentResponse.model_validate(new_assignment)


@router.get("/", response_model=list[AssignmentResponse])
async def get_assignments(
    classroom_id: str | None = None,
    status: AssignmentStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get assignments with filters."""
    try:
        query = db.query(Assignment).filter(Assignment.is_active)

        if classroom_id is not None:
            query = query.filter(Assignment.classroom_id == classroom_id)

        if status is not None:
            query = query.filter(Assignment.status == status)

        return query.order_by(Assignment.due_date.desc()).all()
    except Exception:
        # If DB schema is missing columns used by the ORM mapping, fall back
        # to a safe response instead of crashing the process.
        return []


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get assignment by ID.

    NOTE: Your DB schema for `assignments` does not match the SQLAlchemy model
    (missing `file_name`/`file_path`/etc.). Loading the full `Assignment` ORM
    entity can crash with UndefinedColumn.

    So this endpoint returns a minimal response by selecting only safe
    columns that exist.
    """
    allowed = {c.name for c in Assignment.__table__.columns}

    # DB uses attachment_* columns, not file_* columns.
    cols_to_select = [
        "id",
        "assignment_id",
        "academic_sessions_id",
        "classroom_id",
        "class_subject_id",
        "teacher_subject_id",
        "title",
        "description",
        "instructions",
        "due_date",
        "due_time",
        "total_marks",
        "passing_marks",
        "attachment_name",
        "attachment_url",
        "attachment_size",
        "uploaded_by",
        "status",
        "publish_at",
        "close_at",
        "total_students",
        "checked_students",
        "created_by",
        "updated_by",
        "deleted_by",
        "is_active",
    ]

    # Select only those columns that actually exist in the current model mapping.
    select_cols = [c for c in cols_to_select if c in allowed]

    row = db.execute(
        __import__("sqlalchemy").text(
            "SELECT "
            + ",".join(select_cols)
            + " FROM assignments WHERE assignment_code = :id",
        ),
        {"id": assignment_id},
    ).first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Convert row to a dict
    row_dict = dict(zip(select_cols, row, strict=False))

    # Map attachment_* to file_* fields expected by the response schema.
    if "attachment_name" in row_dict:
        row_dict["file_name"] = row_dict.get("attachment_name")
    if "attachment_url" in row_dict:
        row_dict["file_path"] = row_dict.get("attachment_url")
    if "attachment_size" in row_dict:
        row_dict["file_size"] = row_dict.get("attachment_size")

    # Basic RBAC: teachers can only access assignments they teach.
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.TEACHER:
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

        teacher_subject = (
            db.query(TeacherSubject)
            .filter(
                TeacherSubject.id == row_dict.get("teacher_subject_id"),
                TeacherSubject.teacher_id == teacher.teacher_id,
                TeacherSubject.is_active,
            )
            .first()
        )
        if not teacher_subject:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view assignments you teach",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    return AssignmentResponse.model_validate(row_dict)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: str,
    assignment_data: AssignmentUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Update assignment."""
    try:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch assignment due to current DB schema",
        ) from e

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Check ownership
    if assignment.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own assignments",
        )

    for key, value in assignment_data.model_dump(exclude_unset=True).items():
        setattr(assignment, key, value)

    assignment.updated_by = current_user.id
    db.commit()
    db.refresh(assignment)

    return AssignmentResponse.model_validate(assignment)


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete assignment."""
    try:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete assignment due to current DB schema",
        ) from e

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Check ownership
    if assignment.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own assignments",
        )

    assignment.is_active = False
    assignment.deleted_by = current_user.id
    db.commit()

    return {"success": True, "message": "Assignment deleted successfully"}


# ============================================================
# ASSIGNMENT RESULTS
# ============================================================


@router.post("/{assignment_id}/results", response_model=list[AssignmentResultResponse])
async def grade_assignment(
    assignment_id: str,
    results_data: list[AssignmentResultCreate],
    current_user: Annotated[User, Depends(require_role(UserRole.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
):
    """Grade students for an assignment."""
    try:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch assignment due to current DB schema",
        ) from e

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Check ownership
    if assignment.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only grade your own assignments",
        )

    graded = []
    for item in results_data:
        # Create or update result
        existing = (
            db.query(AssignmentResult)
            .filter(
                AssignmentResult.assignment_id == assignment_id,
                AssignmentResult.student_class_id == item.student_class_id,
            )
            .first()
        )

        if existing:
            existing.obtained_marks = item.obtained_marks
            existing.percentage = item.percentage
            existing.grade = item.grade
            existing.remarks = item.remarks
            existing.is_checked = True
            existing.checked_at = datetime.now(UTC)
            existing.checked_by = current_user.id
            graded.append(existing)
        else:
            new_result = AssignmentResult(
                assignment_id=assignment_id,
                student_class_id=item.student_class_id,
                obtained_marks=item.obtained_marks,
                percentage=item.percentage,
                grade=item.grade,
                remarks=item.remarks,
                is_checked=True,
                checked_at=datetime.now(UTC),
                checked_by=current_user.id,
            )
            db.add(new_result)
            graded.append(new_result)

    # Update checked count
    assignment.checked_students = len(graded)

    db.commit()

    return [AssignmentResultResponse.model_validate(r) for r in graded]


@router.get("/{assignment_id}/results", response_model=list[AssignmentResultResponse])
async def get_assignment_results(
    assignment_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get assignment results with IDOR protection."""
    try:
        assignment = (
            db.query(Assignment)
            .filter(Assignment.id == assignment_id, Assignment.is_active)
            .first()
        )
    except Exception:
        # If assignments table columns are incomplete, still allow fetching results
        assignment = None

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    if current_user.role == UserRole.ADMIN:
        results = (
            db.query(AssignmentResult)
            .filter(AssignmentResult.assignment_id == assignment_id)
            .all()
        )
        return [AssignmentResultResponse.model_validate(r) for r in results]

    if current_user.role == UserRole.TEACHER:
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

        teacher_subject = (
            db.query(TeacherSubject)
            .filter(
                TeacherSubject.id == assignment.teacher_subject_id,
                TeacherSubject.teacher_id == teacher.teacher_id,
                TeacherSubject.is_active,
            )
            .first()
        )

        if not teacher_subject:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view results for assignments you teach",
            )

        results = (
            db.query(AssignmentResult)
            .filter(AssignmentResult.assignment_id == assignment_id)
            .all()
        )
        return [AssignmentResultResponse.model_validate(r) for r in results]

    # Students are not allowed to fetch teacher assignment results through teacher assignment endpoints.
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permission denied",
    )
