# ============================================================
# repositories/core_repositories.py - Core Repositories
# ============================================================

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.enums import UserRole
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
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower().strip()).first()

    def get_by_phone(self, phone: str) -> User | None:
        return self.db.query(User).filter(User.phone == phone).first()

    def get_by_identifier(self, identifier: str) -> User | None:
        return (
            self.db.query(User)
            .filter(
                or_(
                    User.email == identifier.lower().strip(),
                    User.phone == identifier.strip(),
                ),
            )
            .first()
        )

    def get_by_student_id(self, student_id: str) -> User | None:
        return self.db.query(User).filter(User.student_id == student_id).first()

    def get_by_teacher_id(self, teacher_id: str) -> User | None:
        return self.db.query(User).filter(User.teacher_id == teacher_id).first()

    def get_by_admin_id(self, admin_id: str) -> User | None:
        return self.db.query(User).filter(User.admin_id == admin_id).first()

    def get_active_user(self, role: UserRole | None = None) -> list[User]:
        query = self.db.query(User).filter(User.is_active, not User.is_deleted)
        if role:
            query = query.filter(User.role == role)
        return query.all()

    def get_user_by_role(self, role: UserRole) -> list[User]:
        return self.db.query(User).filter(User.role == role).all()

    def search_user(
        self,
        search: str,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> list[User]:
        query = self.db.query(User).filter(
            or_(
                User.email.contains(search.lower().strip()),
                User.phone.contains(search.strip()),
            ),
        )
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.all()

    def update_last_login(self, user_id: int) -> User | None:
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.now(UTC)
            user.login_count += 1
            user.failed_login_count = 0
            self.db.flush()
        return user

    def increment_failed_login(self, user_id: int) -> User | None:
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_count += 1
            self.db.flush()
        return user

    def update_password(self, user_id: int, password_hash: str) -> User | None:
        user = self.get_by_id(user_id)
        if user:
            user.password_hash = password_hash
            user.password_changed_at = datetime.now(UTC)
            self.db.flush()
        return user

    def verify_email(self, user_id: int) -> User | None:
        user = self.get_by_id(user_id)
        if user:
            user.email_verified = True
            user.email_otp = None
            user.email_otp_expiry = None
            self.db.flush()
        return user

    def set_otp(
        self,
        user_id: int,
        otp: str,
        expiry_minutes: int = 10,
    ) -> User | None:
        user = self.get_by_id(user_id)
        if user:
            user.email_otp = otp
            user.email_otp_expiry = datetime.now(UTC) + timedelta(
                minutes=expiry_minutes,
            )
            self.db.flush()
        return user

    def clear_otp(self, user_id: int) -> User | None:
        user = self.get_by_id(user_id)
        if user:
            user.email_otp = None
            user.email_otp_expiry = None
            self.db.flush()
        return user

    def verify_otp(self, user_id: int, otp: str) -> bool:
        user = self.get_by_id(user_id)
        if not user or not user.email_otp:
            return False
        if user.email_otp != otp:
            return False
        return not (user.email_otp_expiry and user.email_otp_expiry < datetime.now(UTC))

    def get_dashboard_stats(self) -> dict[str, Any]:
        return {
            "total_user": self.count(is_deleted=False),
            "active_user": self.count(is_active=True, is_deleted=False),
            "students": self.count(role=UserRole.STUDENT, is_deleted=False),
            "teachers": self.count(role=UserRole.TEACHER, is_deleted=False),
            "admins": self.count(role=UserRole.ADMIN, is_deleted=False),
        }


class StudentProfileRepository(BaseRepository[StudentProfile]):
    """Student profile repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(StudentProfile, db)

    def get_by_user_id(self, user_id: int) -> StudentProfile | None:
        return (
            self.db.query(StudentProfile)
            .filter(StudentProfile.user_id == user_id)
            .first()
        )

    def get_by_student_id(self, student_id: str) -> StudentProfile | None:
        return (
            self.db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .first()
        )

    def get_by_admission_number(
        self,
        admission_number: str,
    ) -> StudentProfile | None:
        return (
            self.db.query(StudentProfile)
            .filter(StudentProfile.admission_number == admission_number)
            .first()
        )

    def search_students(
        self,
        search: str,
        is_active: bool | None = None,
    ) -> list[StudentProfile]:
        query = self.db.query(StudentProfile).filter(
            or_(
                StudentProfile.student_name.contains(search.strip()),
                StudentProfile.student_id.contains(search.strip()),
                StudentProfile.admission_number.contains(search.strip()),
            ),
        )
        if is_active is not None:
            query = query.filter(StudentProfile.is_active == is_active)
        return query.all()

    def get_students_by_class(
        self,
        classroom_id: str,
        session_id: int,
    ) -> list[StudentProfile]:
        from app.model import StudentClass

        return (
            self.db.query(StudentProfile)
            .join(StudentClass, StudentClass.student_id == StudentProfile.student_id)
            .filter(
                StudentClass.classroom_id == classroom_id,
                StudentClass.academic_sessions_id == session_id,
                StudentClass.status == "ACTIVE",
            )
            .all()
        )


class TeacherProfileRepository(BaseRepository[TeacherProfile]):
    """Teacher profile repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(TeacherProfile, db)

    def get_by_user_id(self, user_id: int) -> TeacherProfile | None:
        return (
            self.db.query(TeacherProfile)
            .filter(TeacherProfile.user_id == user_id)
            .first()
        )

    def get_by_teacher_id(self, teacher_id: str) -> TeacherProfile | None:
        return (
            self.db.query(TeacherProfile)
            .filter(TeacherProfile.teacher_id == teacher_id)
            .first()
        )

    def get_by_employee_code(self, employee_code: str) -> TeacherProfile | None:
        return (
            self.db.query(TeacherProfile)
            .filter(TeacherProfile.employee_code == employee_code)
            .first()
        )

    def search_teachers(
        self,
        search: str,
        department: str | None = None,
        is_active: bool | None = None,
    ) -> list[TeacherProfile]:
        query = self.db.query(TeacherProfile).filter(
            or_(
                TeacherProfile.teacher_name.contains(search.strip()),
                TeacherProfile.teacher_id.contains(search.strip()),
                TeacherProfile.employee_code.contains(search.strip()),
            ),
        )
        if department:
            query = query.filter(TeacherProfile.department == department)
        if is_active is not None:
            query = query.filter(TeacherProfile.is_active == is_active)
        return query.all()

    def get_teachers_by_subject(
        self,
        subject_id: str,
        session_id: int,
    ) -> list[TeacherProfile]:
        from app.model import TeacherSubject

        return (
            self.db.query(TeacherProfile)
            .join(
                TeacherSubject,
                TeacherSubject.teacher_id == TeacherProfile.teacher_id,
            )
            .filter(
                TeacherSubject.subject_id == subject_id,
                TeacherSubject.academic_sessions_id == session_id,
            )
            .all()
        )


class AdminProfileRepository(BaseRepository[AdminProfile]):
    """Admin profile repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(AdminProfile, db)

    def get_by_user_id(self, user_id: int) -> AdminProfile | None:
        return (
            self.db.query(AdminProfile).filter(AdminProfile.user_id == user_id).first()
        )

    def get_by_admin_id(self, admin_id: str) -> AdminProfile | None:
        return (
            self.db.query(AdminProfile)
            .filter(AdminProfile.admin_id == admin_id)
            .first()
        )

    def get_super_admins(self) -> list[AdminProfile]:
        return (
            self.db.query(AdminProfile)
            .filter(AdminProfile.super_admin, AdminProfile.is_active)
            .all()
        )


class AcademicSessionRepository(BaseRepository[AcademicSession]):
    """Academic session repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(AcademicSession, db)

    def get_by_code(self, code: str) -> AcademicSession | None:
        return (
            self.db.query(AcademicSession)
            .filter(AcademicSession.session_code == code)
            .first()
        )

    def get_current_session(self) -> AcademicSession | None:
        return (
            self.db.query(AcademicSession)
            .filter(AcademicSession.is_current, AcademicSession.is_active)
            .first()
        )

    def get_active_sessions(self) -> list[AcademicSession]:
        return (
            self.db.query(AcademicSession)
            .filter(AcademicSession.is_active)
            .order_by(AcademicSession.start_year.desc())
            .all()
        )

    def get_session_by_date(self, date_obj: date) -> AcademicSession | None:
        return (
            self.db.query(AcademicSession)
            .filter(
                AcademicSession.start_date <= date_obj,
                AcademicSession.end_date >= date_obj,
                AcademicSession.is_active,
            )
            .first()
        )

    def set_current_session(self, session_id: str) -> AcademicSession | None:
        self.db.query(AcademicSession).update({"is_current": False})
        session = self.get_by_id(session_id)
        if session:
            session.is_current = True
            self.db.flush()
        return session


class ClassRoomRepository(BaseRepository[ClassRoom]):
    """Classroom repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(ClassRoom, db)

    def get_by_code(self, code: str, session_id: str) -> ClassRoom | None:
        return (
            self.db.query(ClassRoom)
            .filter(
                ClassRoom.class_code == code,
                ClassRoom.academic_sessions_id == session_id,
            )
            .first()
        )

    def get_classes_by_session(self, session_id: str) -> list[ClassRoom]:
        return (
            self.db.query(ClassRoom)
            .filter(
                ClassRoom.academic_sessions_id == session_id,
                ClassRoom.is_active,
            )
            .order_by(ClassRoom.class_name, ClassRoom.section)
            .all()
        )

    def get_classes_by_teacher(
        self,
        teacher_id: str,
        session_id: str,
    ) -> list[ClassRoom]:
        from app.model import TeacherSubject

        return (
            self.db.query(ClassRoom)
            .join(TeacherSubject, TeacherSubject.classroom_id == ClassRoom.class_code)
            .filter(
                TeacherSubject.teacher_id == teacher_id,
                TeacherSubject.academic_sessions_id == session_id,
                ClassRoom.is_active,
            )
            .distinct()
            .all()
        )


class SubjectRepository(BaseRepository[Subject]):
    """Subject repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(Subject, db)

    def get_by_code(self, code: str) -> Subject | None:
        return self.db.query(Subject).filter(Subject.subject_code == code).first()

    def get_by_name(self, name: str) -> Subject | None:
        return self.db.query(Subject).filter(Subject.subject_name == name).first()

    def get_active_subjects(self) -> list[Subject]:
        return (
            self.db.query(Subject)
            .filter(Subject.is_active)
            .order_by(Subject.display_order)
            .all()
        )


class ClassSubjectRepository(BaseRepository[ClassSubject]):
    """Class subject repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(ClassSubject, db)

    def get_by_class_subject(
        self,
        classroom_id: str,
        subject_id: str,
        session_id: int,
    ) -> ClassSubject | None:
        return (
            self.db.query(ClassSubject)
            .filter(
                ClassSubject.classroom_id == classroom_id,
                ClassSubject.subject_id == subject_id,
                ClassSubject.academic_sessions_id == session_id,
            )
            .first()
        )

    def get_subjects_by_class(
        self,
        classroom_id: str,
        session_id: int,
    ) -> list[ClassSubject]:
        return (
            self.db.query(ClassSubject)
            .filter(
                ClassSubject.classroom_id == classroom_id,
                ClassSubject.academic_sessions_id == session_id,
                ClassSubject.is_active,
            )
            .order_by(ClassSubject.display_order)
            .all()
        )


class TeacherSubjectRepository(BaseRepository[TeacherSubject]):
    """Teacher subject repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(TeacherSubject, db)

    def get_by_teacher_class_subject(
        self,
        teacher_id: str,
        classroom_id: str,
        subject_id: str,
        session_id: int,
    ) -> TeacherSubject | None:
        return (
            self.db.query(TeacherSubject)
            .filter(
                TeacherSubject.teacher_id == teacher_id,
                TeacherSubject.classroom_id == classroom_id,
                TeacherSubject.subject_id == subject_id,
                TeacherSubject.academic_sessions_id == session_id,
            )
            .first()
        )

    def get_by_teacher(self, teacher_id: str, session_id: str) -> list[TeacherSubject]:
        return (
            self.db.query(TeacherSubject)
            .filter(
                TeacherSubject.teacher_id == teacher_id,
                TeacherSubject.academic_sessions_id == session_id,
                TeacherSubject.is_active,
            )
            .all()
        )

    def get_by_class(self, classroom_id: str, session_id: int) -> list[TeacherSubject]:
        return (
            self.db.query(TeacherSubject)
            .filter(
                TeacherSubject.classroom_id == classroom_id,
                TeacherSubject.academic_sessions_id == session_id,
                TeacherSubject.is_active,
            )
            .all()
        )


class StudentClassRepository(BaseRepository[StudentClass]):
    """Student class repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(StudentClass, db)

    def get_by_student_session(
        self,
        student_id: str,
        session_id: str,
    ) -> StudentClass | None:
        return (
            self.db.query(StudentClass)
            .filter(
                StudentClass.student_id == student_id,
                StudentClass.academic_sessions_id == session_id,
            )
            .first()
        )

    def get_students_by_class(
        self,
        classroom_id: str,
        session_id: int,
    ) -> list[StudentClass]:
        return (
            self.db.query(StudentClass)
            .filter(
                StudentClass.classroom_id == classroom_id,
                StudentClass.academic_sessions_id == session_id,
                StudentClass.status == "ACTIVE",
            )
            .order_by(StudentClass.roll_number)
            .all()
        )

    def get_active_students_by_class(
        self,
        classroom_id: str,
        session_id: int,
    ) -> list[StudentClass]:
        return self.get_students_by_class(classroom_id, session_id)
