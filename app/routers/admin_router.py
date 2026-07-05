# from fastapi import APIRouter
# from fastapi import Depends
# from fastapi import HTTPException

# from sqlalchemy.orm import Session
# from sqlalchemy import or_

# from app.api.database import SessionLocal

# from app.model import (
#     User,
#     StudentProfile,
#     TeacherProfile
# )

# from app.schemas import (
#     AdminCreateStudentSchema,
#     AdminCreateTeacherSchema,
#     usertatusUpdate
# )

# from app.dependencies import (
#     get_current_admin,
#     get_db
# )

# from app.auth import (
#     hash_password
# )


# router = APIRouter(
#     prefix="/admin",
#     tags=["Admin"]
# )

# @router.post("/students")
# def create_student(
#     data: AdminCreateStudentSchema,
#     admin=Depends(get_current_admin)
# ):
#     db: Session = Depends(get_db)

#     try:

#         existing = db.query(User).filter(
#             or_(
#                 User.email == data.email,
#                 User.phone == data.phone
#             )
#         ).first()
    
#         if existing:

#             raise HTTPException(
#                 status_code=400,
#                 detail="User already exists"
#             )
    
#         user = User(
        
#             username=data.email,
    
#             email=data.email,
    
#             phone=data.phone,

#             password_hash=hash_password(
#                 data.password
#             ),

#             role="student"
#         )

#         db.add(user)

#         db.commit()

#         db.refresh(user)


#     student_id = f"STU{user.id:06d}"

#     user.student_id = student_id

#     db.commit()
    

#     profile = StudentProfile(

#             student_id=student_id,

#             user_id=user.id,

#             student_name=data.student_name,

#             student_email=user.email,

#             student_phone=user.phone
#         )

#     db.add(profile)

#     db.commit()

#     return {

#         "message":
#         "Student created",

#         "student_id":
#         student_id
#     }
    


# @router.post("/teachers")
# def create_teacher(
#     data: AdminCreateTeacherSchema,
#     admin=Depends(get_current_admin)
# ):
#     db: Session = Depends(get_db)

#     try:

#         existing = db.query(User).filter(
#             or_(
#                 User.email == data.email,
#                 User.phone == data.phone
#             )
#         ).first()
    
#         if existing:

#             raise HTTPException(
#                 status_code=400,
#                 detail="User already exists"
#             )
    
#         user = User(
        
#             username=data.email,
    
#             email=data.email,
    
#             phone=data.phone,

#             password_hash=hash_password(
#                 data.password
#             ),

#             role="teacher"
#         )

#         db.add(user)

#         db.commit()

#         db.refresh(user)


#     teacher_id = f"TEA{user.id:06d}"

#     user.teacher_id = teacher_id

#     db.commit()
    

#     profile = TeacherProfile(

#             teacher_id=teacher_id,

#             user_id=user.id,

#             teacher_name=data.teacher_name,

#             teacher_email=user.email,

#             teacher_phone=user.phone,

#             qualification=data.qualification,

#             department=data.department
#         )

#     db.add(profile)

#     db.commit()

#     return {

#         "message":
#         "Teacher created",

#         "teacher_id":
#         teacher_id
#     }



# @router.get("/user")
# def list_user(
#     admin=Depends(get_current_admin)
# ):
#     db: Session = Depends(get_db)

#     user = db.query(User).all()

#     return user


# @router.get("/user/{user_id}")
# def get_user(
#     user_id: int,
#     admin=Depends(get_current_admin)
# ):
#     user = db.query(User).filter(
#         User.id == user_id
#     ).first()
#     return{
#         "id": user.id,
#         "role": user.role,
#         "email": user.email,
#         "phone": user.phone,
#         "student_id": user.student_id,
#         "teacher_id": user.teacher_id,
#         "is_active": user.is_active
#     }


# @router.put(
#     "/user/{user_id}/status"
# )
# def update_status(
#     user_id:int,
#     data:usertatusUpdate,
#     admin=Depends(get_current_admin)
# ):
#     user.is_active = data.is_active

#     db.commit()

#     return {
#         "message":"updated"
#     }



# @router.get("/dashboard")
# def admin_dashboard(
#     admin=Depends(get_current_admin)
# ):
#     total_user = db.query(User).count()

#     total_students = db.query(User).filter(
#         User.role == "student"
#     ).count()

#     total_teachers = db.query(User).filter(
#         User.role == "teacher"
#     ).count()

#     return {
#         "role":"admin",
#         "total_user":total_user,
#         "total_students":total_students,
#         "total_teachers":total_teachers
#     }


# ============================================================
# routers/admin_router.py - Admin Management Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.database import get_db
from app.model import User, AdminProfile, StudentProfile, TeacherProfile, AcademicSession, ClassRoom, Subject
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserMinResponse,
    AdminProfileCreate,
    AdminProfileUpdate,
    AdminProfileResponse,
    StudentProfileCreate,
    StudentProfileResponse,
    TeacherProfileCreate,
    TeacherProfileResponse,
    AcademicSessionCreate,
    AcademicSessionUpdate,
    AcademicSessionResponse,
    ClassRoomCreate,
    ClassRoomUpdate,
    ClassRoomResponse,
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    TeacherSubjectCreate,
    TeacherSubjectResponse,
    StudentClassCreate,
    StudentClassResponse,
    PaginatedResponseSchema,
    ResponseSchema
)
from app.auth import hash_password
from app.dependencies import (
    get_current_user,
    require_role,
    require_super_admin
)
from app.core.enums import UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])

# ============================================================
# USER MANAGEMENT
# ============================================================

@router.post("/user", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new user (Admin only).
    """
    # Check if email exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone exists
    existing = db.query(User).filter(User.phone == user_data.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user
    new_user = User(
        email=user_data.email,
        phone=user_data.phone,
        role=user_data.role,
        password_hash=hash_password(user_data.password),
        created_by=current_user.id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Assign the role-specific business ID now that new_user.id is known.
    # StudentProfile/TeacherProfile/AdminProfile FK to these columns, so they
    # must be populated before a profile row can be created for this user.
    from app.helpers.code_generators import (
        generate_student_id, generate_teacher_id, generate_admin_id
    )
    if user_data.role == UserRole.STUDENT:
        new_user.student_id = generate_student_id(new_user.id)
    elif user_data.role == UserRole.TEACHER:
        new_user.teacher_id = generate_teacher_id(new_user.id)
    elif user_data.role == UserRole.ADMIN:
        new_user.admin_id = generate_admin_id(new_user.id)
    db.commit()
    db.refresh(new_user)
    
    # Create profile based on role
    if user_data.role == UserRole.STUDENT:
        # Student profile will be created separately
        pass
    elif user_data.role == UserRole.TEACHER:
        # Teacher profile will be created separately
        pass
    elif user_data.role == UserRole.ADMIN:
        # Admin profile will be created separately
        pass
    
    return UserResponse.model_validate(new_user)

@router.get("/user", response_model=PaginatedResponseSchema[UserResponse])
async def list_user(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List all user with pagination and filters.
    """
    query = db.query(User)
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if search:
        query = query.filter(
            User.email.contains(search) |
            User.phone.contains(search)
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    user = query.offset(offset).limit(page_size).all()
    
    return {
        "success": True,
        "data": [UserResponse.model_validate(u) for u in user],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "total_items": total
        }
    }

@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)

@router.put("/user/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update user details.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_data.email is not None:
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_data.email
    
    if user_data.phone is not None:
        existing = db.query(User).filter(
            User.phone == user_data.phone,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already in use"
            )
        user.phone = user_data.phone
    
    if user_data.profile_photo is not None:
        user.profile_photo = user_data.profile_photo
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.device_token is not None:
        user.device_token = user_data.device_token
    
    user.updated_by = current_user.id
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.delete("/user/{user_id}")
async def delete_user(
    user_id: int,
    soft_delete: bool = True,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete user (soft or hard delete).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    if soft_delete:
        user.is_deleted = True
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        user.deleted_by = current_user.id
        db.commit()
        return {"success": True, "message": "User soft deleted"}
    else:
        db.delete(user)
        db.commit()
        return {"success": True, "message": "User permanently deleted"}

# ============================================================
# ADMIN PROFILE MANAGEMENT
# ============================================================

@router.post("/admin-profiles", response_model=AdminProfileResponse)
async def create_admin_profile(
    profile_data: AdminProfileCreate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    Create admin profile.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == profile_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if profile exists
    existing = db.query(AdminProfile).filter(
        AdminProfile.user_id == profile_data.user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin profile already exists"
        )
    
    # Generate admin_id if not provided
    admin_id = profile_data.admin_id or f"ADM{datetime.now().year}{datetime.now().month:02d}{user.id:04d}"
    
    new_profile = AdminProfile(
        admin_id=admin_id,
        user_id=profile_data.user_id,
        admin_name=profile_data.admin_name,
        designation=profile_data.designation,
        phone=profile_data.phone,
        profile_photo=profile_data.profile_photo,
        notes=profile_data.notes,
        can_create_admin=profile_data.can_create_admin,
        super_admin=profile_data.super_admin
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return AdminProfileResponse.model_validate(new_profile)


@router.post("/student-profiles", response_model=StudentProfileResponse)
async def create_student_profile(
    profile_data: StudentProfileCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a student profile for an existing user with role=student.
    """
    user = db.query(User).filter(User.id == profile_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have the student role"
        )

    existing = db.query(StudentProfile).filter(
        StudentProfile.user_id == profile_data.user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile already exists"
        )

    if not user.student_id:
        from app.helpers.code_generators import generate_student_id
        user.student_id = generate_student_id(user.id)
        db.commit()
        db.refresh(user)

    new_profile = StudentProfile(
        student_id=user.student_id,
        user_id=user.id,
        student_name=profile_data.student_name,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        blood_group=profile_data.blood_group,
        profile_photo=profile_data.profile_photo,
        school_name=profile_data.school_name,
        school_address=profile_data.school_address,
        medium=profile_data.medium,
        board=profile_data.board,
        address=profile_data.address,
        city=profile_data.city,
        state=profile_data.state,
        pincode=profile_data.pincode,
        parent_name=profile_data.parent_name,
        parent_phone=profile_data.parent_phone,
        guardian_name=profile_data.guardian_name,
        guardian_phone=profile_data.guardian_phone,
        emergency_contact=profile_data.emergency_contact,
        admission_date=profile_data.admission_date,
        remarks=profile_data.remarks,
        admission_number=profile_data.admission_number,
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return StudentProfileResponse.model_validate(new_profile)


@router.post("/teacher-profiles", response_model=TeacherProfileResponse)
async def create_teacher_profile(
    profile_data: TeacherProfileCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a teacher profile for an existing user with role=teacher.
    """
    user = db.query(User).filter(User.id == profile_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have the teacher role"
        )

    existing = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == profile_data.user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher profile already exists"
        )

    if not user.teacher_id:
        from app.helpers.code_generators import generate_teacher_id
        user.teacher_id = generate_teacher_id(user.id)
        db.commit()
        db.refresh(user)

    new_profile = TeacherProfile(
        teacher_id=user.teacher_id,
        user_id=user.id,
        teacher_name=profile_data.teacher_name,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        qualification=profile_data.qualification,
        experience_years=profile_data.experience_years,
        specialization=profile_data.specialization,
        profile_photo=profile_data.profile_photo,
        employee_code=profile_data.employee_code,
        joining_date=profile_data.joining_date,
        designation=profile_data.designation,
        department=profile_data.department,
        address=profile_data.address,
        city=profile_data.city,
        state=profile_data.state,
        pincode=profile_data.pincode,
        emergency_contact=profile_data.emergency_contact,
        remarks=profile_data.remarks,
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return TeacherProfileResponse.model_validate(new_profile)

@router.get("/admin-profiles", response_model=List[AdminProfileResponse])
async def list_admin_profiles(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List all admin profiles.
    """
    profiles = db.query(AdminProfile).all()
    return [AdminProfileResponse.model_validate(p) for p in profiles]

# ============================================================
# ACADEMIC SESSION MANAGEMENT
# ============================================================

@router.post("/academic-sessions", response_model=AcademicSessionResponse)
async def create_academic_sessions(
    session_data: AcademicSessionCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new academic session.
    """
    # Check if code exists
    existing = db.query(AcademicSession).filter(
        AcademicSession.session_code == session_data.session_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session code already exists"
        )
    
    # If this session is current, deactivate others
    if session_data.is_current:
        db.query(AcademicSession).update({"is_current": False})
    
    new_session = AcademicSession(
        session_code=session_data.session_code,
        session_name=session_data.session_name,
        start_year=session_data.start_year,
        end_year=session_data.end_year,
        start_date=session_data.start_date,
        end_date=session_data.end_date,
        is_current=session_data.is_current,
        description=session_data.description,
        created_by=current_user.id
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return AcademicSessionResponse.model_validate(new_session)

@router.get("/academic-sessions", response_model=List[AcademicSessionResponse])
async def list_academic_sessions(
    is_current: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all academic sessions.
    """
    
    query = db.query(AcademicSession)
    if is_current is not None:
        query = query.filter(AcademicSession.is_current == is_current)
    
    sessions = query.order_by(AcademicSession.start_year.desc()).all()
    return [AcademicSessionResponse.model_validate(s) for s in sessions]

# ============================================================
# CLASSROOM MANAGEMENT
# ============================================================

@router.post("/classrooms", response_model=ClassRoomResponse)
async def create_classroom(
    class_data: ClassRoomCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new classroom.
    """
    
    # Check session exists
    session = db.query(AcademicSession).filter(
        AcademicSession.id == class_data.academic_sessions_id
    ).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found"
        )
    
    # Check if class exists in session
    existing = db.query(ClassRoom).filter(
        ClassRoom.academic_sessions_id == class_data.academic_sessions_id,
        ClassRoom.class_code == class_data.class_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class already exists in this session"
        )
    
    new_class = ClassRoom(
        academic_sessions_id=class_data.academic_sessions_id,
        class_code=class_data.class_code,
        class_name=class_data.class_name,
        section=class_data.section,
        display_name=class_data.display_name,
        description=class_data.description,
        class_teacher_id=class_data.class_teacher_id,
        created_by=current_user.id
    )
    
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return ClassRoomResponse.model_validate(new_class)

@router.get("/classrooms", response_model=List[ClassRoomResponse])
async def list_classrooms(
    academic_sessions_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all classrooms.
    """
    from app.model import ClassRoom
    
    query = db.query(ClassRoom)
    if academic_sessions_id:
        query = query.filter(ClassRoom.academic_sessions_id == academic_sessions_id)
    
    classrooms = query.order_by(ClassRoom.class_name, ClassRoom.section).all()
    return [ClassRoomResponse.model_validate(c) for c in classrooms]

# ============================================================
# SUBJECT MANAGEMENT
# ============================================================

@router.post("/subjects", response_model=SubjectResponse)
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

@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all subjects.
    """
    
    query = db.query(Subject)
    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)
    
    subjects = query.order_by(Subject.display_order).all()
    return [SubjectResponse.model_validate(s) for s in subjects]

# ============================================================
# TEACHER SUBJECT MAPPING
# ============================================================

@router.post("/teacher-subjects", response_model=TeacherSubjectResponse)
async def assign_teacher_to_subject(
    mapping_data: TeacherSubjectCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Assign a teacher to a subject.
    """
    from app.model import TeacherSubject, ClassSubject, TeacherProfile
    
    # Check teacher exists
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.teacher_id == mapping_data.teacher_id
    ).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check class subject exists
    class_subject = db.query(ClassSubject).filter(
        ClassSubject.id == mapping_data.class_subject_id
    ).first()
    if not class_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class subject not found"
        )
    
    # Check if mapping exists
    existing = db.query(TeacherSubject).filter(
        TeacherSubject.academic_sessions_id == mapping_data.academic_sessions_id,
        TeacherSubject.classroom_id == mapping_data.classroom_id,
        TeacherSubject.subject_id == mapping_data.subject_id,
        TeacherSubject.teacher_id == mapping_data.teacher_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher already assigned to this subject"
        )
    
    new_mapping = TeacherSubject(
        academic_sessions_id=mapping_data.academic_sessions_id,
        class_subject_id=mapping_data.class_subject_id,
        classroom_id=mapping_data.classroom_id,
        subject_id=mapping_data.subject_id,
        teacher_id=mapping_data.teacher_id,
        is_class_teacher=mapping_data.is_class_teacher,
        remarks=mapping_data.remarks
    )
    
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    
    return TeacherSubjectResponse.model_validate(new_mapping)

# ============================================================
# STUDENT CLASS ENROLLMENT
# ============================================================

@router.post("/student-classes", response_model=StudentClassResponse)
async def enroll_student(
    enrollment_data: StudentClassCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Enroll a student in a class.
    """
    from app.model import StudentClass, StudentProfile, ClassRoom
    
    # Check student exists
    student = db.query(StudentProfile).filter(
        StudentProfile.student_id == enrollment_data.student_id
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check classroom exists
    classroom = db.query(ClassRoom).filter(
        ClassRoom.id == enrollment_data.classroom_id
    ).first()
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    # Check if already enrolled in session
    existing = db.query(StudentClass).filter(
        StudentClass.academic_sessions_id == enrollment_data.academic_sessions_id,
        StudentClass.student_id == enrollment_data.student_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already enrolled in this session"
        )
    
    # Check roll number uniqueness
    roll_exists = db.query(StudentClass).filter(
        StudentClass.academic_sessions_id == enrollment_data.academic_sessions_id,
        StudentClass.classroom_id == enrollment_data.classroom_id,
        StudentClass.roll_number == enrollment_data.roll_number
    ).first()
    if roll_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roll number already taken in this class"
        )
    
    new_enrollment = StudentClass(
        academic_sessions_id=enrollment_data.academic_sessions_id,
        student_id=enrollment_data.student_id,
        classroom_id=enrollment_data.classroom_id,
        roll_number=enrollment_data.roll_number,
        admission_date=enrollment_data.admission_date,
        status=enrollment_data.status,
        roll_number_locked=enrollment_data.roll_number_locked,
        remarks=enrollment_data.remarks
    )
    
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return StudentClassResponse.model_validate(new_enrollment)

# ============================================================
# SYSTEM HEALTH
# ============================================================

@router.get("/system/health")
async def system_health(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    System health check.
    """
    from app.api.database import test_db_connection
    
    db_status = test_db_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/system/statistics")
async def system_statistics(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get system statistics.
    """
    
    total_user = db.query(User).count()
    total_students = db.query(StudentProfile).count()
    total_teachers = db.query(TeacherProfile).count()
    total_classes = db.query(ClassRoom).filter(ClassRoom.is_active == True).count()
    total_subjects = db.query(Subject).filter(Subject.is_active == True).count()
    
    return {
        "total_user": total_user,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "timestamp": datetime.utcnow().isoformat()
    }
