from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.core.enums import UserRole
from app.helpers.code_generators import (
    generate_admin_id,
    generate_student_id,
    generate_teacher_id,
)
from app.model import (
    AcademicSession,
    AdminProfile,
    ClassRoom,
    ClassSubject,
    StudentClass,
    StudentProfile,
    Subject,
    TeacherProfile,
    TeacherSubject,
    User,
)
from app.schemas import (
    AcademicSessionCreate,
    ClassRoomCreate,
    StudentClassCreate,
    SubjectCreate,
    TeacherSubjectCreate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.identifier_resolver_service import IdentifierResolverService
from app.services.registration_number_service import RegistrationNumberService


def _paginate(page: int, page_size: int) -> tuple[int, int]:
    offset = (page - 1) * page_size
    return offset, page_size


class AdminUserService:
    def __init__(self, db: Session, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def create_user(self, user_data: UserCreate) -> User:
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if self.db.query(User).filter(User.phone == user_data.phone).first():
            raise HTTPException(
                status_code=400,
                detail="Phone number already registered",
            )

        new_user = User(
            email=user_data.email,
            phone=user_data.phone,
            role=user_data.role,
            password_hash=hash_password(user_data.password),
            created_by=self.current_user.id,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        if user_data.role == UserRole.STUDENT:
            new_user.student_id = generate_student_id(new_user.id)
        elif user_data.role == UserRole.TEACHER:
            new_user.teacher_id = generate_teacher_id(new_user.id)
        elif user_data.role == UserRole.ADMIN:
            new_user.admin_id = generate_admin_id(new_user.id)
        self.db.commit()
        self.db.refresh(new_user)

        try:
            name_hint = (
                new_user.email.split("@")[0].replace(".", " ").replace("_", " ").title()
            )

            if user_data.role == UserRole.STUDENT:
                if (
                    self.db.query(StudentProfile)
                    .filter(StudentProfile.user_id == new_user.id)
                    .first()
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Student profile already exists",
                    )
                profile = StudentProfile(
                    student_id=new_user.student_id,
                    user_id=new_user.id,
                    student_name=name_hint,
                    school_name="",
                    created_by=self.current_user.id,
                )
                self.db.add(profile)
                self.db.flush()
                RegistrationNumberService(self.db).generate_for_student(
                    profile,
                    commit=False,
                )

            elif user_data.role == UserRole.TEACHER:
                if (
                    self.db.query(TeacherProfile)
                    .filter(TeacherProfile.user_id == new_user.id)
                    .first()
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Teacher profile already exists",
                    )
                profile = TeacherProfile(
                    teacher_id=new_user.teacher_id,
                    user_id=new_user.id,
                    teacher_name=name_hint,
                    created_by=self.current_user.id,
                )
                self.db.add(profile)

            elif user_data.role == UserRole.ADMIN:
                if (
                    self.db.query(AdminProfile)
                    .filter(AdminProfile.user_id == new_user.id)
                    .first()
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Admin profile already exists",
                    )
                profile = AdminProfile(
                    admin_id=new_user.admin_id,
                    user_id=new_user.id,
                    admin_name=name_hint,
                    created_by=self.current_user.id,
                )
                self.db.add(profile)

            self.db.commit()
            self.db.refresh(new_user)

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"User created but profile creation failed: {exc}",
            ) from exc

        return new_user

    def list_users(
        self,
        page: int,
        page_size: int,
        role: UserRole | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> dict:
        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            query = query.filter(
                User.email.contains(search) | User.phone.contains(search),
            )
        total = query.count()
        offset, limit = _paginate(page, page_size)
        users = query.offset(offset).limit(limit).all()
        return {
            "success": True,
            "data": [UserResponse.model_validate(u) for u in users],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "total_items": total,
            },
        }

    def get_user(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user_data.email is not None:
            if (
                self.db.query(User)
                .filter(User.email == user_data.email, User.id != user_id)
                .first()
            ):
                raise HTTPException(status_code=400, detail="Email already in use")
            user.email = user_data.email
        if user_data.phone is not None:
            if (
                self.db.query(User)
                .filter(User.phone == user_data.phone, User.id != user_id)
                .first()
            ):
                raise HTTPException(status_code=400, detail="Phone already in use")
            user.phone = user_data.phone
        if user_data.profile_photo is not None:
            user.profile_photo = user_data.profile_photo
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.device_token is not None:
            user.device_token = user_data.device_token

        user.updated_by = self.current_user.id
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int, soft_delete: bool = True) -> dict:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.id == self.current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete your own account",
            )

        if soft_delete:
            user.is_deleted = True
            user.is_active = False
            user.deleted_at = datetime.now(UTC)
            user.deleted_by = self.current_user.id
            self.db.commit()
            return {"success": True, "message": "User soft deleted"}
        self.db.delete(user)
        self.db.commit()
        return {"success": True, "message": "User permanently deleted"}


class AdminProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_profiles(self) -> list[AdminProfile]:
        return self.db.query(AdminProfile).all()


class AcademicSessionService:
    def __init__(self, db: Session, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def create(self, data: AcademicSessionCreate) -> AcademicSession:
        if (
            self.db.query(AcademicSession)
            .filter(AcademicSession.session_code == data.session_code)
            .first()
        ):
            raise HTTPException(status_code=400, detail="Session code already exists")
        if data.is_current:
            self.db.query(AcademicSession).update({"is_current": False})
        session = AcademicSession(
            session_code=data.session_code,
            session_name=data.session_name,
            start_year=data.start_year,
            end_year=data.end_year,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
            description=data.description,
            created_by=self.current_user.id,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list(self, is_current: bool | None = None) -> list[AcademicSession]:
        query = self.db.query(AcademicSession)
        if is_current is not None:
            query = query.filter(AcademicSession.is_current == is_current)
        return query.order_by(AcademicSession.start_year.desc()).all()


class ClassroomService:
    def __init__(self, db: Session, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def create(self, data: ClassRoomCreate) -> ClassRoom:
        session = (
            self.db.query(AcademicSession)
            .filter(AcademicSession.session_code == data.academic_sessions_id)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Academic session not found")
        if (
            self.db.query(ClassRoom)
            .filter(
                ClassRoom.academic_sessions_id == data.academic_sessions_id,
                ClassRoom.class_code == data.class_code,
            )
            .first()
        ):
            raise HTTPException(
                status_code=400,
                detail="Class already exists in this session",
            )

        resolved_teacher_id = None
        if data.class_teacher_id:
            resolved_teacher_id = IdentifierResolverService(self.db).resolve_teacher_id(
                data.class_teacher_id,
            )

        new_class = ClassRoom(
            academic_sessions_id=data.academic_sessions_id,
            class_code=data.class_code,
            class_name=data.class_name,
            section=data.section,
            display_name=data.display_name,
            description=data.description,
            class_teacher_id=resolved_teacher_id,
            created_by=self.current_user.id,
        )
        self.db.add(new_class)
        self.db.commit()
        self.db.refresh(new_class)
        return new_class

    def list(self, academic_sessions_id: str | None = None) -> list[ClassRoom]:
        query = self.db.query(ClassRoom)
        if academic_sessions_id:
            query = query.filter(ClassRoom.academic_sessions_id == academic_sessions_id)
        return query.order_by(ClassRoom.class_name, ClassRoom.section).all()


class SubjectService:
    def __init__(self, db: Session, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def create(self, data: SubjectCreate) -> Subject:
        if (
            self.db.query(Subject)
            .filter(Subject.subject_code == data.subject_code)
            .first()
        ):
            raise HTTPException(status_code=400, detail="Subject code already exists")
        subject = Subject(
            subject_code=data.subject_code,
            subject_name=data.subject_name,
            description=data.description,
            display_order=data.display_order,
            subject_type=data.subject_type,
            created_by=self.current_user.id,
        )
        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)
        return subject

    def list(self, is_active: bool | None = None) -> list[Subject]:
        query = self.db.query(Subject)
        if is_active is not None:
            query = query.filter(Subject.is_active == is_active)
        return query.order_by(Subject.display_order).all()


class TeacherSubjectService:
    def __init__(self, db: Session, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def assign(self, data: TeacherSubjectCreate) -> TeacherSubject:
        resolver = IdentifierResolverService(self.db)
        teacher = resolver.resolve_teacher(data.teacher_id)
        data.teacher_id = teacher.teacher_id

        class_subject = (
            self.db.query(ClassSubject)
            .filter(ClassSubject.id == data.class_subject_id)
            .first()
        )
        if not class_subject:
            raise HTTPException(status_code=404, detail="Class subject not found")

        if (
            self.db.query(TeacherSubject)
            .filter(
                TeacherSubject.academic_sessions_id == data.academic_sessions_id,
                TeacherSubject.classroom_id == data.classroom_id,
                TeacherSubject.subject_id == data.subject_id,
                TeacherSubject.teacher_id == data.teacher_id,
            )
            .first()
        ):
            raise HTTPException(
                status_code=400,
                detail="Teacher already assigned to this subject",
            )

        mapping = TeacherSubject(
            academic_sessions_id=data.academic_sessions_id,
            class_subject_id=data.class_subject_id,
            classroom_id=data.classroom_id,
            subject_id=data.subject_id,
            teacher_id=data.teacher_id,
            is_class_teacher=data.is_class_teacher,
            remarks=data.remarks,
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def list(
        self,
        academic_sessions_id: str | None = None,
        classroom_id: str | None = None,
        teacher_id: str | None = None,
    ) -> list[TeacherSubject]:
        query = self.db.query(TeacherSubject)
        if academic_sessions_id:
            query = query.filter(
                TeacherSubject.academic_sessions_id == academic_sessions_id,
            )
        if classroom_id:
            query = query.filter(TeacherSubject.classroom_id == classroom_id)
        if teacher_id:
            query = query.filter(TeacherSubject.teacher_id == teacher_id)
        return query.order_by(TeacherSubject.id).all()


class StudentClassService:
    def __init__(self, db: Session, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def enroll(self, data: StudentClassCreate) -> StudentClass:
        resolver = IdentifierResolverService(self.db)
        student = resolver.resolve_student(data.student_id)
        data.student_id = student.student_id

        classroom = (
            self.db.query(ClassRoom)
            .filter(ClassRoom.class_code == data.classroom_id)
            .first()
        )
        if not classroom:
            raise HTTPException(status_code=404, detail="Classroom not found")

        if (
            self.db.query(StudentClass)
            .filter(
                StudentClass.academic_sessions_id == data.academic_sessions_id,
                StudentClass.student_id == data.student_id,
            )
            .first()
        ):
            raise HTTPException(
                status_code=400,
                detail="Student already enrolled in this session",
            )

        if (
            self.db.query(StudentClass)
            .filter(
                StudentClass.academic_sessions_id == data.academic_sessions_id,
                StudentClass.classroom_id == data.classroom_id,
                StudentClass.roll_number == data.roll_number,
            )
            .first()
        ):
            raise HTTPException(
                status_code=400,
                detail="Roll number already taken in this class",
            )

        enrollment = StudentClass(
            academic_sessions_id=data.academic_sessions_id,
            student_id=data.student_id,
            classroom_id=data.classroom_id,
            roll_number=data.roll_number,
            admission_date=data.admission_date,
            status=data.status,
            roll_number_locked=data.roll_number_locked,
            remarks=data.remarks,
        )
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment

    def list(
        self,
        academic_sessions_id: str | None = None,
        classroom_id: str | None = None,
        student_id: str | None = None,
    ) -> list[StudentClass]:
        query = self.db.query(StudentClass)
        if academic_sessions_id:
            query = query.filter(
                StudentClass.academic_sessions_id == academic_sessions_id,
            )
        if classroom_id:
            query = query.filter(StudentClass.classroom_id == classroom_id)
        if student_id:
            query = query.filter(StudentClass.student_id == student_id)
        return query.order_by(StudentClass.id).all()


class AdminStatsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def statistics(self) -> dict:
        return {
            "total_user": self.db.query(User).count(),
            "total_students": self.db.query(StudentProfile).count(),
            "total_teachers": self.db.query(TeacherProfile).count(),
            "total_classes": self.db.query(ClassRoom)
            .filter(ClassRoom.is_active)
            .count(),
            "total_subjects": self.db.query(Subject).filter(Subject.is_active).count(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
