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

#     assignment_id: int,

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

#     assignment_id: int,

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

#     assignment_id: int,

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

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.database import get_db
from app.model import User, Assignment,TeacherProfile, TeacherSubject, ClassRoom, AssignmentResult
from app.schemas import (
    AssignmentResponse,
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResultResponse,
    AssignmentResultCreate,
    AssignmentResultUpdate,
    ResponseSchema,
    PaginatedResponseSchema
)
from app.dependencies import (
    get_current_user,
    get_current_teacher_profile,
    require_role
)
from app.core.enums import UserRole, AssignmentStatus

router = APIRouter(prefix="/assignments", tags=["Assignments"])

# ============================================================
# ASSIGNMENT CRUD
# ============================================================

@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Create a new assignment.
    """
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Verify teacher is assigned to this class
    teacher_subject = db.query(TeacherSubject).filter(
        TeacherSubject.id == assignment_data.teacher_subject_id,
        TeacherSubject.teacher_id == teacher.teacher_id
    ).first()
    
    if not teacher_subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class"
        )
    
    new_assignment = Assignment(
        assignment_id=assignment_data.assignment_id,
        academic_sessions_id=assignment_data.academic_sessions_id,
        classroom_id=assignment_data.classroom_id,
        class_subject_id=assignment_data.class_subject_id,
        teacher_subject_id=assignment_data.teacher_subject_id,
        title=assignment_data.title,
        description=assignment_data.description,
        instructions=assignment_data.instructions,
        due_date=assignment_data.due_date,
        due_time=assignment_data.due_time,
        total_marks=assignment_data.total_marks,
        passing_marks=assignment_data.passing_marks,
        attachment_name=assignment_data.attachment_name,
        attachment_url=assignment_data.attachment_url,
        attachment_size=assignment_data.attachment_size,
        status=assignment_data.status,
        publish_at=assignment_data.publish_at,
        close_at=assignment_data.close_at,
        created_by=current_user.id
    )
    
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    return AssignmentResponse.model_validate(new_assignment)

@router.get("/", response_model=List[AssignmentResponse])
async def get_assignments(
    classroom_id: Optional[int] = None,
    status: Optional[AssignmentStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get assignments with filters.
    """
    query = db.query(Assignment)
    
    if classroom_id:
        query = query.filter(Assignment.classroom_id == classroom_id)
    
    if status:
        query = query.filter(Assignment.status == status)
    
    # For teachers, only show their assignments
    if current_user.role == UserRole.TEACHER:
        teacher = db.query(TeacherProfile).filter(
            TeacherProfile.user_id == current_user.id
        ).first()
        if teacher:
            teacher_subject_ids = db.query(TeacherSubject.id).filter(
                TeacherSubject.teacher_id == teacher.teacher_id
            )
            query = query.filter(Assignment.teacher_subject_id.in_(teacher_subject_ids))
    
    assignments = query.order_by(Assignment.created_at.desc()).all()
    return [AssignmentResponse.model_validate(a) for a in assignments]

@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get assignment by ID.
    """
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return AssignmentResponse.model_validate(assignment)

@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Update assignment.
    """
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check ownership
    if assignment.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own assignments"
        )
    
    for key, value in assignment_data.dict(exclude_unset=True).items():
        setattr(assignment, key, value)
    
    assignment.updated_by = current_user.id
    db.commit()
    db.refresh(assignment)
    
    return AssignmentResponse.model_validate(assignment)

@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Delete assignment.
    """
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check ownership
    if assignment.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own assignments"
        )
    
    assignment.is_active = False
    assignment.deleted_by = current_user.id
    db.commit()
    
    return {"success": True, "message": "Assignment deleted successfully"}

# ============================================================
# ASSIGNMENT RESULTS
# ============================================================

@router.post("/{assignment_id}/results", response_model=List[AssignmentResultResponse])
async def grade_assignment(
    assignment_id: int,
    results_data: List[AssignmentResultCreate],
    current_user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db)
):
    """
    Grade students for an assignment.
    """
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check ownership
    if assignment.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only grade your own assignments"
        )
    
    graded = []
    for item in results_data:
        # Create or update result
        existing = db.query(AssignmentResult).filter(
            AssignmentResult.assignment_id == assignment_id,
            AssignmentResult.student_class_id == item.student_class_id
        ).first()
        
        if existing:
            existing.obtained_marks = item.obtained_marks
            existing.percentage = item.percentage
            existing.grade = item.grade
            existing.remarks = item.remarks
            existing.is_checked = True
            existing.checked_at = datetime.utcnow()
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
                checked_at=datetime.utcnow(),
                checked_by=current_user.id
            )
            db.add(new_result)
            graded.append(new_result)
    
    # Update checked count
    assignment.checked_students = len(graded)
    
    db.commit()
    
    return [AssignmentResultResponse.model_validate(r) for r in graded]

@router.get("/{assignment_id}/results", response_model=List[AssignmentResultResponse])
async def get_assignment_results(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get results for an assignment.
    """
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.TEACHER:
        teacher = db.query(TeacherProfile).filter(
            TeacherProfile.user_id == current_user.id
        ).first()
        teacher_subject = db.query(TeacherSubject).filter(
            TeacherSubject.id == assignment.teacher_subject_id,
            TeacherSubject.teacher_id == teacher.teacher_id if teacher else None
        ).first()
        if not teacher_subject:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view results for your assignments"
            )
    
    results = db.query(AssignmentResult).filter(
        AssignmentResult.assignment_id == assignment_id
    ).all()
    
    return [AssignmentResultResponse.model_validate(r) for r in results]
