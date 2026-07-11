

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
    StudentProfileResponse,
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
    ResponseSchema,
    PaginatedTeacherAdminListResponse,
    PaginatedStudentAdminListResponse,
    TeacherAdminListResponse,
    StudentAdminListResponse,
)

from app.auth import hash_password
from app.dependencies import (
    get_current_user,
    require_role,
    require_super_admin
)
from app.core.enums import UserRole
from app.services.admin_student_teacher_service import AdminStudentTeacherService


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
    
    # ----------------------------------------------------------------
    # AUTO-CREATE role-specific profile in the SAME transaction
    # - Prevent duplicate profile rows
    # ----------------------------------------------------------------
    try:
        if user_data.role == UserRole.STUDENT:
            # Prevent duplicate profile creation
            existing_profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == new_user.id
            ).first()
            if existing_profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student profile already exists for this user"
                )

            # Extract name hint from email prefix (updated by student later)
            name_hint = new_user.email.split("@")[0].replace(".", " ").replace("_", " ").title()
            student_profile = StudentProfile(
                student_id=new_user.student_id,
                user_id=new_user.id,
                student_name=name_hint,
                school_name="",          # placeholder – student updates later
                created_by=current_user.id
            )
            db.add(student_profile)
            db.flush()  # get the row into the transaction before generating registration_number

            from app.services.registration_number_service import RegistrationNumberService
            RegistrationNumberService(db).generate_for_student(student_profile, commit=False)

        elif user_data.role == UserRole.TEACHER:
            # Prevent duplicate profile creation
            existing_profile = db.query(TeacherProfile).filter(
                TeacherProfile.user_id == new_user.id
            ).first()
            if existing_profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Teacher profile already exists for this user"
                )

            name_hint = new_user.email.split("@")[0].replace(".", " ").replace("_", " ").title()
            teacher_profile = TeacherProfile(
                teacher_id=new_user.teacher_id,
                user_id=new_user.id,
                teacher_name=name_hint,
                created_by=current_user.id
            )
            db.add(teacher_profile)

        elif user_data.role == UserRole.ADMIN:
            # Prevent duplicate profile creation
            existing_profile = db.query(AdminProfile).filter(
                AdminProfile.user_id == new_user.id
            ).first()
            if existing_profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admin profile already exists for this user"
                )

            name_hint = new_user.email.split("@")[0].replace(".", " ").replace("_", " ").title()
            admin_profile = AdminProfile(
                admin_id=new_user.admin_id,
                user_id=new_user.id,
                admin_name=name_hint,
                created_by=current_user.id
            )
            db.add(admin_profile)

        db.commit()
        db.refresh(new_user)

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User created but profile creation failed: {exc}"
        )


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

# NOTE:
# Manual admin profile creation endpoint removed.
# AdminProfile is auto-created automatically during POST /admin/user



# POST /admin/student-profiles  → REMOVED (profile auto-created on POST /admin/user)
# POST /admin/teacher-profiles  → REMOVED (profile auto-created on POST /admin/user)

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

    # class_teacher_id ab teacher_id, email, ya naam - teeno accept karta hai
    resolved_class_teacher_id = None
    if class_data.class_teacher_id:
        from app.services.identifier_resolver_service import IdentifierResolverService
        resolved_class_teacher_id = IdentifierResolverService(db).resolve_teacher_id(class_data.class_teacher_id)

    new_class = ClassRoom(
        academic_sessions_id=class_data.academic_sessions_id,
        class_code=class_data.class_code,
        class_name=class_data.class_name,
        section=class_data.section,
        display_name=class_data.display_name,
        description=class_data.description,
        class_teacher_id=resolved_class_teacher_id,
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
    from app.services.identifier_resolver_service import IdentifierResolverService

    # teacher_id field ab teacher_id, email, ya naam accept karta hai
    teacher = IdentifierResolverService(db).resolve_teacher(mapping_data.teacher_id)
    mapping_data.teacher_id = teacher.teacher_id  # normalize to the real business id

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

@router.get("/teacher-subjects", response_model=List[TeacherSubjectResponse])
async def list_teacher_subjects(
    academic_sessions_id: Optional[int] = None,
    classroom_id: Optional[int] = None,
    teacher_id: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List teacher-subject assignment mappings.
    """
    from app.model import TeacherSubject

    query = db.query(TeacherSubject)
    if academic_sessions_id:
        query = query.filter(TeacherSubject.academic_sessions_id == academic_sessions_id)
    if classroom_id:
        query = query.filter(TeacherSubject.classroom_id == classroom_id)
    if teacher_id:
        query = query.filter(TeacherSubject.teacher_id == teacher_id)

    mappings = query.order_by(TeacherSubject.id).all()
    return [TeacherSubjectResponse.model_validate(m) for m in mappings]

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
    from app.services.identifier_resolver_service import IdentifierResolverService

    # student_id field ab student_id, email, ya naam accept karta hai
    student = IdentifierResolverService(db).resolve_student(enrollment_data.student_id)
    enrollment_data.student_id = student.student_id  # normalize to the real business id

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

@router.get("/student-classes", response_model=List[StudentClassResponse])
async def list_student_classes(
    academic_sessions_id: Optional[int] = None,
    classroom_id: Optional[int] = None,
    student_id: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List student-class enrollment records.
    """
    from app.model import StudentClass

    query = db.query(StudentClass)
    if academic_sessions_id:
        query = query.filter(StudentClass.academic_sessions_id == academic_sessions_id)
    if classroom_id:
        query = query.filter(StudentClass.classroom_id == classroom_id)
    if student_id:
        query = query.filter(StudentClass.student_id == student_id)

    enrollments = query.order_by(StudentClass.id).all()
    return [StudentClassResponse.model_validate(e) for e in enrollments]

# ============================================================
# FLAT PROFILE LISTS (raw, non-paginated — used by internal tooling)
# ============================================================

@router.get("/student-profiles", response_model=List[StudentProfileResponse])
async def list_student_profiles_flat(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List all student profiles as a flat (non-paginated) list.
    """
    profiles = db.query(StudentProfile).all()
    return [StudentProfileResponse.model_validate(p) for p in profiles]


@router.get("/teacher-profiles", response_model=List[TeacherProfileResponse])
async def list_teacher_profiles_flat(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List all teacher profiles as a flat (non-paginated) list.
    """
    profiles = db.query(TeacherProfile).all()
    return [TeacherProfileResponse.model_validate(p) for p in profiles]

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

@router.get("/teachers", response_model=PaginatedTeacherAdminListResponse)
async def list_admin_teachers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    department: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """List teachers for admin (pagination + search + filters)."""
    service = AdminStudentTeacherService(db)
    return service.list_teachers_admin(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        department=department,
    )


@router.get("/students", response_model=PaginatedStudentAdminListResponse)
async def list_admin_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    class_id: Optional[int] = Query(None, ge=1),
    class_code: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """List students for admin (pagination + search + class filter)."""
    service = AdminStudentTeacherService(db)
    return service.list_students_admin(
        page=page,
        page_size=page_size,
        search=search,
        class_id=class_id,
        class_code=class_code,
    )


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
