# from fastapi import APIRouter
# from fastapi import Depends
# from fastapi import HTTPException

# from sqlalchemy import func

# from sqlalchemy.orm import Session

# from app.model import (
#     User,
#     Subject,
#     SubjectProgress,
#     StudentProfile
# )

# from app.schemas import (
#     SubjectCreate,
#     SubjectResponse,
#     SubjectProgressCreate,
#     SubjectProgressResponse
# )

# from app.dependencies import (
#     get_db,
#     get_current_student,
#     require_role
# )
# def normalize_subject_name(name: str) -> str:
#     return name.strip().title()

# router = APIRouter(
#     prefix="/subjects",
#     tags=["Subjects"]
# )

# def teacher_or_admin():
#     return require_role(
#         "teacher",
#         "admin"
#     )
# # =====================================================
# # CREATE SUBJECT

# @router.post(
#     "/",
#     response_model=SubjectResponse
# )
# def create_subject(

#     data: SubjectCreate,

#     current_user: User = Depends(
#         teacher_or_admin()
#     ),

#     db: Session = Depends(get_db)
# ):

#     normalized_name = normalize_subject_name(
#     data.subject_name
#     )

#     existing = (
#         db.query(Subject)
#         .filter(
#             func.lower(Subject.subject_name)
#             == normalized_name.lower()
#         )
#         .first()
#     )

#     if existing:
#         raise HTTPException(
#             status_code=400,
#             detail="Subject already exists"
#         )
    
#     subject = Subject(
#         subject_name=normalized_name
#     )

#     db.add(subject)

#     db.commit()

#     db.refresh(subject)

#     return subject


# # =====================================================
# # GET ALL SUBJECTS
# # =====================================================

# @router.get(
#     "/",
#     response_model=list[SubjectResponse]
# )
# def get_subjects(

#     db: Session = Depends(get_db)

# ):

#     return db.query(
#         Subject
#     ).all()


# # =====================================================
# # CREATE SUBJECT PROGRESS




# @router.post(
#     "/progress/{student_id}",
#     response_model=SubjectProgressResponse
# )
# def create_subject_progress(

#     student_id: str,

#     data: SubjectProgressCreate,
#     current_user: User = Depends(
#         teacher_or_admin()
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

#     existing = (

#         db.query(SubjectProgress)

#         .filter(
#             SubjectProgress.student_id
#             == student.student_id,


#             SubjectProgress.subject_id
#             == data.subject_id
#         )

#         .first()
#     )

#     if existing:

#         raise HTTPException(
#             status_code=400,
#             detail="Progress already exists"
#         )

#     progress = SubjectProgress(

#         student_id=student.student_id,


#         subject_id=data.subject_id,

#         total_chapters=data.total_chapters,

#         completed_chapters=data.completed_chapters,

#         total_classes=data.total_classes,

#         attended_classes=data.attended_classes
#     )

#     db.add(progress)

#     db.commit()

#     db.refresh(progress)

#     return SubjectProgressResponse(
#         id=progress.id,
#         subject_name=(progress.subject.subject_name if progress.subject else ""),
#         total_chapters=progress.total_chapters,
#         completed_chapters=progress.completed_chapters,
#         total_classes=progress.total_classes,
#         attended_classes=progress.attended_classes,
#     )




# # =====================================================
# # UPDATE SUBJECT PROGRESS
# # =====================================================


# @router.put(
#     "/progress/{student_id}/{subject_id}",
#     response_model=SubjectProgressResponse
# )
# def update_subject_progress(

#     student_id: str,

#     subject_id: int,

#     data: SubjectProgressCreate,
#     current_user: User = Depends(
#         teacher_or_admin()
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

#     progress = (

#         db.query(SubjectProgress)

#         .filter(
#             SubjectProgress.student_id
#             == student.student_id,

#             SubjectProgress.subject_id
#             == subject_id

#         )

#         .first()
#     )

#     if not progress:

#         raise HTTPException(
#             status_code=404,
#             detail="Progress not found"
#         )

#     progress.total_chapters = data.total_chapters

#     progress.completed_chapters = data.completed_chapters

#     progress.total_classes = data.total_classes

#     progress.attended_classes = data.attended_classes

#     db.commit()

#     db.refresh(progress)

#     return SubjectProgressResponse(
#         id=progress.id,
#         subject_name=(progress.subject.subject_name if progress.subject else ""),
#         total_chapters=progress.total_chapters,
#         completed_chapters=progress.completed_chapters,
#         total_classes=progress.total_classes,
#         attended_classes=progress.attended_classes,
#     )


# # =====================================================
# # STUDENT VIEW PROGRESS
# # =====================================================

# @router.get(
#     "/my-progress",
#     response_model=list[SubjectProgressResponse]
# )
# def my_progress(
#     current_user: User = Depends(
#         require_role("student")
#     ),
#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     progresses = (

#         db.query(
#             SubjectProgress
#         )

#         .filter(
#             SubjectProgress.student_id
#             == student.student_id

#         )

#         .all()
#     )

#     return [
#         SubjectProgressResponse(
#             id=p.id,
#             subject_name=(p.subject.subject_name if p.subject else ""),

#             total_chapters=p.total_chapters,
#             completed_chapters=p.completed_chapters,
#             total_classes=p.total_classes,
#             attended_classes=p.attended_classes,
#         )
#         for p in progresses
#     ]



# ============================================================
# routers/subject_routers.py - Subject Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.database import get_db
from app.model import User, Subject, ClassSubject, ClassRoom, AcademicSession
from app.schemas import (
    SubjectResponse,
    SubjectCreate,
    SubjectUpdate,
    ClassSubjectResponse,
    ClassSubjectCreate,
    ClassRoomMinResponse,
    AcademicSessionMinResponse
)
from app.dependencies import (
    get_current_user,
    require_role
)
from app.core.enums import UserRole

router = APIRouter(prefix="/subjects", tags=["Subjects"])

# ============================================================
# SUBJECT CRUD
# ============================================================

@router.post("/", response_model=SubjectResponse)
async def create_subject(
    subject_data: SubjectCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new subject.
    """
    # Check if code exists
    existing = db.query(Subject).filter(
        Subject.subject_code == subject_data.subject_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject code already exists"
        )
    
    new_subject = Subject(
        subject_code=subject_data.subject_code,
        subject_name=subject_data.subject_name,
        description=subject_data.description,
        display_order=subject_data.display_order,
        subject_type=subject_data.subject_type,
        created_by=current_user.id
    )
    
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    
    return SubjectResponse.model_validate(new_subject)

@router.get("/", response_model=List[SubjectResponse])
async def get_subjects(
    is_active: Optional[bool] = None,
    subject_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all subjects.
    """
    query = db.query(Subject)
    
    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)
    
    if subject_type:
        query = query.filter(Subject.subject_type == subject_type)
    
    subjects = query.order_by(Subject.display_order, Subject.subject_name).all()
    return [SubjectResponse.model_validate(s) for s in subjects]

@router.get("/{subject_id:int}", response_model=SubjectResponse)
async def get_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get subject by ID.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return SubjectResponse.model_validate(subject)

@router.put("/{subject_id:int}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update subject.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    for key, value in subject_data.dict(exclude_unset=True).items():
        setattr(subject, key, value)
    
    subject.updated_by = current_user.id
    db.commit()
    db.refresh(subject)
    
    return SubjectResponse.model_validate(subject)

@router.delete("/{subject_id:int}")
async def delete_subject(
    subject_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete subject (soft delete).
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check if subject is in use
    class_subject = db.query(ClassSubject).filter(
        ClassSubject.subject_id == subject_id
    ).first()
    if class_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject is in use and cannot be deleted"
        )
    
    subject.is_active = False
    subject.updated_by = current_user.id
    db.commit()
    
    return {"success": True, "message": "Subject deleted successfully"}

# ============================================================
# CLASS SUBJECT MAPPING
# ============================================================

@router.post("/class-subjects", response_model=ClassSubjectResponse)
async def assign_subject_to_class(
    mapping_data: ClassSubjectCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Assign a subject to a class.
    """
    # Check class exists
    classroom = db.query(ClassRoom).filter(
        ClassRoom.id == mapping_data.classroom_id
    ).first()
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    # Check subject exists
    subject = db.query(Subject).filter(
        Subject.id == mapping_data.subject_id
    ).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check if mapping exists
    existing = db.query(ClassSubject).filter(
        ClassSubject.academic_sessions_id == mapping_data.academic_sessions_id,
        ClassSubject.classroom_id == mapping_data.classroom_id,
        ClassSubject.subject_id == mapping_data.subject_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject already assigned to this class"
        )
    
    new_mapping = ClassSubject(
        academic_sessions_id=mapping_data.academic_sessions_id,
        classroom_id=mapping_data.classroom_id,
        subject_id=mapping_data.subject_id,
        display_order=mapping_data.display_order,
        created_by=current_user.id
    )
    
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    
    return ClassSubjectResponse.model_validate(new_mapping)

@router.get("/class-subjects", response_model=List[ClassSubjectResponse])
async def get_class_subjects(
    academic_sessions_id: Optional[int] = None,
    classroom_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get class-subject mappings.
    """
    query = db.query(ClassSubject)
    
    if academic_sessions_id:
        query = query.filter(ClassSubject.academic_sessions_id == academic_sessions_id)
    
    if classroom_id:
        query = query.filter(ClassSubject.classroom_id == classroom_id)
    
    mappings = query.order_by(ClassSubject.display_order).all()
    return [ClassSubjectResponse.model_validate(m) for m in mappings]

@router.get("/classes/{classroom_id}/subjects", response_model=List[SubjectResponse])
async def get_subjects_for_class(
    classroom_id: int,
    academic_sessions_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get subjects assigned to a specific class.
    """
    query = db.query(Subject).join(
        ClassSubject,
        ClassSubject.subject_id == Subject.id
    ).filter(
        ClassSubject.classroom_id == classroom_id
    )
    
    if academic_sessions_id:
        query = query.filter(ClassSubject.academic_sessions_id == academic_sessions_id)
    
    subjects = query.order_by(ClassSubject.display_order).all()
    return [SubjectResponse.model_validate(s) for s in subjects]

@router.delete("/class-subjects/{mapping_id}")
async def remove_class_subject(
    mapping_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Remove a class-subject mapping.
    """
    mapping = db.query(ClassSubject).filter(
        ClassSubject.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )
    
    # Check if mapping is in use
    from app.model import TeacherSubject
    teacher_subject = db.query(TeacherSubject).filter(
        TeacherSubject.class_subject_id == mapping_id
    ).first()
    if teacher_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove mapping as it is assigned to a teacher"
        )
    
    db.delete(mapping)
    db.commit()
    
    return {"success": True, "message": "Class-subject mapping removed"}
