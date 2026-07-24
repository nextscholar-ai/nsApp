from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import get_current_user, require_role
from app.model import User
from app.schemas import (
    AcademicSessionCreate,
    AcademicSessionResponse,
    AdminProfileResponse,
    ClassRoomCreate,
    ClassRoomResponse,
    PaginatedResponseSchema,
    PaginatedStudentAdminListResponse,
    PaginatedTeacherAdminListResponse,
    StudentClassCreate,
    StudentClassResponse,
    StudentProfileResponse,
    SubjectCreate,
    SubjectResponse,
    TeacherProfileResponse,
    TeacherSubjectCreate,
    TeacherSubjectResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.admin_service import (
    AcademicSessionService,
    AdminProfileService,
    AdminStatsService,
    AdminUserService,
    ClassroomService,
    StudentClassService,
    SubjectService,
    TeacherSubjectService,
)
from app.services.admin_student_teacher_service import AdminStudentTeacherService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/user", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = AdminUserService(db, current_user)
    return UserResponse.model_validate(service.create_user(user_data))


@router.get("/user", response_model=PaginatedResponseSchema[UserResponse])
async def list_user(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    role: UserRole | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = AdminUserService(db, current_user)
    return service.list_users(page, page_size, role, is_active, search)


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = AdminUserService(db, current_user)
    return UserResponse.model_validate(service.get_user(user_id))


@router.put("/user/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = AdminUserService(db, current_user)
    return UserResponse.model_validate(service.update_user(user_id, user_data))


@router.delete("/user/{user_id}")
async def delete_user(
    user_id: int,
    soft_delete: bool = True,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = AdminUserService(db, current_user)
    return service.delete_user(user_id, soft_delete)


@router.get("/admin-profiles", response_model=list[AdminProfileResponse])
async def list_admin_profiles(
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = AdminProfileService(db)
    return [AdminProfileResponse.model_validate(p) for p in service.list_profiles()]


@router.post("/academic-sessions", response_model=AcademicSessionResponse)
async def create_academic_sessions(
    session_data: AcademicSessionCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = AcademicSessionService(db, current_user)
    return AcademicSessionResponse.model_validate(service.create(session_data))


@router.get("/academic-sessions", response_model=list[AcademicSessionResponse])
async def list_academic_sessions(
    is_current: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AcademicSessionService(db, current_user)
    return [AcademicSessionResponse.model_validate(s) for s in service.list(is_current)]


@router.post("/classrooms", response_model=ClassRoomResponse)
async def create_classroom(
    class_data: ClassRoomCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = ClassroomService(db, current_user)
    return ClassRoomResponse.model_validate(service.create(class_data))


@router.get("/classrooms", response_model=list[ClassRoomResponse])
async def list_classrooms(
    academic_sessions_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassroomService(db, current_user)
    return [
        ClassRoomResponse.model_validate(c) for c in service.list(academic_sessions_id)
    ]


@router.post("/subjects", response_model=SubjectResponse)
async def create_subject(
    subject_data: SubjectCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = SubjectService(db, current_user)
    return SubjectResponse.model_validate(service.create(subject_data))


@router.get("/subjects", response_model=list[SubjectResponse])
async def list_subjects(
    is_active: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SubjectService(db, current_user)
    return [SubjectResponse.model_validate(s) for s in service.list(is_active)]


@router.post("/teacher-subjects", response_model=TeacherSubjectResponse)
async def assign_teacher_to_subject(
    mapping_data: TeacherSubjectCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = TeacherSubjectService(db, current_user)
    return TeacherSubjectResponse.model_validate(service.assign(mapping_data))


@router.get("/teacher-subjects", response_model=list[TeacherSubjectResponse])
async def list_teacher_subjects(
    academic_sessions_id: int | None = None,
    classroom_id: int | None = None,
    teacher_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = TeacherSubjectService(db, current_user)
    return [
        TeacherSubjectResponse.model_validate(m)
        for m in service.list(academic_sessions_id, classroom_id, teacher_id)
    ]


@router.post("/student-classes", response_model=StudentClassResponse)
async def enroll_student(
    enrollment_data: StudentClassCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = StudentClassService(db, current_user)
    return StudentClassResponse.model_validate(service.enroll(enrollment_data))


@router.get("/student-classes", response_model=list[StudentClassResponse])
async def list_student_classes(
    academic_sessions_id: int | None = None,
    classroom_id: int | None = None,
    student_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    service = StudentClassService(db, current_user)
    return [
        StudentClassResponse.model_validate(e)
        for e in service.list(academic_sessions_id, classroom_id, student_id)
    ]


@router.get("/student-profiles", response_model=list[StudentProfileResponse])
async def list_student_profiles_flat(
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    from app.model import StudentProfile

    profiles = db.query(StudentProfile).all()
    return [StudentProfileResponse.model_validate(p) for p in profiles]


@router.get("/teacher-profiles", response_model=list[TeacherProfileResponse])
async def list_teacher_profiles_flat(
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    from app.model import TeacherProfile

    profiles = db.query(TeacherProfile).all()
    return [TeacherProfileResponse.model_validate(p) for p in profiles]


@router.get("/system/health")
async def system_health(
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
):
    from app.api.database import test_db_connection

    db_status = test_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/teachers", response_model=PaginatedTeacherAdminListResponse)
async def list_admin_teachers(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    is_active: bool | None = None,
    department: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
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
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    class_id: Annotated[int | None, Query(ge=1)] = None,
    class_code: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
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
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    service = AdminStatsService(db)
    return service.statistics()
