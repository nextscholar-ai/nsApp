# ============================================================
# repositories/core_repositories.py - Core Repositories
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import datetime, date, timedelta

from app.model import (
    User, StudentProfile, TeacherProfile, AdminProfile,
    AcademicSession, ClassRoom, Subject, ClassSubject, TeacherSubject,
    StudentClass, StudentPromotionHistory
)

from app.repositories.base_repository import BaseRepository
from app.core.enums import UserRole


class UserRepository(BaseRepository[User]):
    """User repository."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower().strip()).first()
    
    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()
    
    def get_by_identifier(self, identifier: str) -> Optional[User]:
        return self.db.query(User).filter(
            or_(User.email == identifier.lower().strip(), User.phone == identifier.strip())
        ).first()
    
    def get_by_student_id(self, student_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.student_id == student_id).first()
    
    def get_by_teacher_id(self, teacher_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.teacher_id == teacher_id).first()
    
    def get_by_admin_id(self, admin_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.admin_id == admin_id).first()
    
    def get_active_user(self, role: Optional[UserRole] = None) -> List[User]:
        query = self.db.query(User).filter(User.is_active == True, User.is_deleted == False)
        if role:
            query = query.filter(User.role == role)
        return query.all()
    
    def get_user_by_role(self, role: UserRole) -> List[User]:
        return self.db.query(User).filter(User.role == role).all()
    
    def search_user(self, search: str, role: Optional[UserRole] = None, is_active: Optional[bool] = None) -> List[User]:
        query = self.db.query(User).filter(
            or_(User.email.contains(search.lower().strip()), User.phone.contains(search.strip()))
        )
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.all()
    
    def update_last_login(self, user_id: int) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            user.login_count += 1
            user.failed_login_count = 0
            self.db.flush()
        return user
    
    def increment_failed_login(self, user_id: int) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_count += 1
            self.db.flush()
        return user
    
    def update_password(self, user_id: int, password_hash: str) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.password_hash = password_hash
            user.password_changed_at = datetime.utcnow()
            self.db.flush()
        return user
    
    def verify_email(self, user_id: int) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.email_verified = True
            user.email_otp = None
            user.email_otp_expiry = None
            self.db.flush()
        return user
    
    def set_otp(self, user_id: int, otp: str, expiry_minutes: int = 10) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.email_otp = otp
            user.email_otp_expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
            self.db.flush()
        return user
    
    def clear_otp(self, user_id: int) -> Optional[User]:
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
        if user.email_otp_expiry and user.email_otp_expiry < datetime.utcnow():
            return False
        return True
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        return {
            "total_user": self.count(is_deleted=False),
            "active_user": self.count(is_active=True, is_deleted=False),
            "students": self.count(role=UserRole.STUDENT, is_deleted=False),
            "teachers": self.count(role=UserRole.TEACHER, is_deleted=False),
            "admins": self.count(role=UserRole.ADMIN, is_deleted=False)
        }


class StudentProfileRepository(BaseRepository[StudentProfile]):
    """Student profile repository."""
    
    def __init__(self, db: Session):
        super().__init__(StudentProfile, db)
    
    def get_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        return self.db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    
    def get_by_student_id(self, student_id: str) -> Optional[StudentProfile]:
        return self.db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
    
    def get_by_admission_number(self, admission_number: str) -> Optional[StudentProfile]:
        return self.db.query(StudentProfile).filter(StudentProfile.admission_number == admission_number).first()
    
    def search_students(self, search: str, is_active: Optional[bool] = None) -> List[StudentProfile]:
        query = self.db.query(StudentProfile).filter(
            or_(
                StudentProfile.student_name.contains(search.strip()),
                StudentProfile.student_id.contains(search.strip()),
                StudentProfile.admission_number.contains(search.strip())
            )
        )
        if is_active is not None:
            query = query.filter(StudentProfile.is_active == is_active)
        return query.all()
    
    def get_students_by_class(self, classroom_id: int, session_id: int) -> List[StudentProfile]:
        from app.model import StudentClass
        return self.db.query(StudentProfile).join(
            StudentClass, StudentClass.student_id == StudentProfile.student_id
        ).filter(
            StudentClass.classroom_id == classroom_id,
            StudentClass.academic_sessions_id == session_id,
            StudentClass.status == "ACTIVE"
        ).all()


class TeacherProfileRepository(BaseRepository[TeacherProfile]):
    """Teacher profile repository."""
    
    def __init__(self, db: Session):
        super().__init__(TeacherProfile, db)
    
    def get_by_user_id(self, user_id: int) -> Optional[TeacherProfile]:
        return self.db.query(TeacherProfile).filter(TeacherProfile.user_id == user_id).first()
    
    def get_by_teacher_id(self, teacher_id: str) -> Optional[TeacherProfile]:
        return self.db.query(TeacherProfile).filter(TeacherProfile.teacher_id == teacher_id).first()
    
    def get_by_employee_code(self, employee_code: str) -> Optional[TeacherProfile]:
        return self.db.query(TeacherProfile).filter(TeacherProfile.employee_code == employee_code).first()
    
    def search_teachers(self, search: str, department: Optional[str] = None, is_active: Optional[bool] = None) -> List[TeacherProfile]:
        query = self.db.query(TeacherProfile).filter(
            or_(
                TeacherProfile.teacher_name.contains(search.strip()),
                TeacherProfile.teacher_id.contains(search.strip()),
                TeacherProfile.employee_code.contains(search.strip())
            )
        )
        if department:
            query = query.filter(TeacherProfile.department == department)
        if is_active is not None:
            query = query.filter(TeacherProfile.is_active == is_active)
        return query.all()
    
    def get_teachers_by_subject(self, subject_id: int, session_id: int) -> List[TeacherProfile]:
        from app.model import TeacherSubject
        return self.db.query(TeacherProfile).join(
            TeacherSubject, TeacherSubject.teacher_id == TeacherProfile.teacher_id
        ).filter(
            TeacherSubject.subject_id == subject_id,
            TeacherSubject.academic_sessions_id == session_id
        ).all()


class AdminProfileRepository(BaseRepository[AdminProfile]):
    """Admin profile repository."""
    
    def __init__(self, db: Session):
        super().__init__(AdminProfile, db)
    
    def get_by_user_id(self, user_id: int) -> Optional[AdminProfile]:
        return self.db.query(AdminProfile).filter(AdminProfile.user_id == user_id).first()
    
    def get_by_admin_id(self, admin_id: str) -> Optional[AdminProfile]:
        return self.db.query(AdminProfile).filter(AdminProfile.admin_id == admin_id).first()
    
    def get_super_admins(self) -> List[AdminProfile]:
        return self.db.query(AdminProfile).filter(
            AdminProfile.super_admin == True,
            AdminProfile.is_active == True
        ).all()


class AcademicSessionRepository(BaseRepository[AcademicSession]):
    """Academic session repository."""
    
    def __init__(self, db: Session):
        super().__init__(AcademicSession, db)
    
    def get_by_code(self, code: str) -> Optional[AcademicSession]:
        return self.db.query(AcademicSession).filter(AcademicSession.session_code == code).first()
    
    def get_current_session(self) -> Optional[AcademicSession]:
        return self.db.query(AcademicSession).filter(
            AcademicSession.is_current == True,
            AcademicSession.is_active == True
        ).first()
    
    def get_active_sessions(self) -> List[AcademicSession]:
        return self.db.query(AcademicSession).filter(
            AcademicSession.is_active == True
        ).order_by(AcademicSession.start_year.desc()).all()
    
    def get_session_by_date(self, date_obj: date) -> Optional[AcademicSession]:
        return self.db.query(AcademicSession).filter(
            AcademicSession.start_date <= date_obj,
            AcademicSession.end_date >= date_obj,
            AcademicSession.is_active == True
        ).first()
    
    def set_current_session(self, session_id: int) -> Optional[AcademicSession]:
        self.db.query(AcademicSession).update({"is_current": False})
        session = self.get_by_id(session_id)
        if session:
            session.is_current = True
            self.db.flush()
        return session


class ClassRoomRepository(BaseRepository[ClassRoom]):
    """Classroom repository."""
    
    def __init__(self, db: Session):
        super().__init__(ClassRoom, db)
    
    def get_by_code(self, code: str, session_id: int) -> Optional[ClassRoom]:
        return self.db.query(ClassRoom).filter(
            ClassRoom.class_code == code,
            ClassRoom.academic_sessions_id == session_id
        ).first()
    
    def get_classes_by_session(self, session_id: int) -> List[ClassRoom]:
        return self.db.query(ClassRoom).filter(
            ClassRoom.academic_sessions_id == session_id,
            ClassRoom.is_active == True
        ).order_by(ClassRoom.class_name, ClassRoom.section).all()
    
    def get_classes_by_teacher(self, teacher_id: str, session_id: int) -> List[ClassRoom]:
        from app.model import TeacherSubject
        return self.db.query(ClassRoom).join(
            TeacherSubject, TeacherSubject.classroom_id == ClassRoom.id
        ).filter(
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.academic_sessions_id == session_id,
            ClassRoom.is_active == True
        ).distinct().all()


class SubjectRepository(BaseRepository[Subject]):
    """Subject repository."""
    
    def __init__(self, db: Session):
        super().__init__(Subject, db)
    
    def get_by_code(self, code: str) -> Optional[Subject]:
        return self.db.query(Subject).filter(Subject.subject_code == code).first()
    
    def get_by_name(self, name: str) -> Optional[Subject]:
        return self.db.query(Subject).filter(Subject.subject_name == name).first()
    
    def get_active_subjects(self) -> List[Subject]:
        return self.db.query(Subject).filter(
            Subject.is_active == True
        ).order_by(Subject.display_order).all()


class ClassSubjectRepository(BaseRepository[ClassSubject]):
    """Class subject repository."""
    
    def __init__(self, db: Session):
        super().__init__(ClassSubject, db)
    
    def get_by_class_subject(self, classroom_id: int, subject_id: int, session_id: int) -> Optional[ClassSubject]:
        return self.db.query(ClassSubject).filter(
            ClassSubject.classroom_id == classroom_id,
            ClassSubject.subject_id == subject_id,
            ClassSubject.academic_sessions_id == session_id
        ).first()
    
    def get_subjects_by_class(self, classroom_id: int, session_id: int) -> List[ClassSubject]:
        return self.db.query(ClassSubject).filter(
            ClassSubject.classroom_id == classroom_id,
            ClassSubject.academic_sessions_id == session_id,
            ClassSubject.is_active == True
        ).order_by(ClassSubject.display_order).all()


class TeacherSubjectRepository(BaseRepository[TeacherSubject]):
    """Teacher subject repository."""
    
    def __init__(self, db: Session):
        super().__init__(TeacherSubject, db)
    
    def get_by_teacher_class_subject(self, teacher_id: str, classroom_id: int, subject_id: int, session_id: int) -> Optional[TeacherSubject]:
        return self.db.query(TeacherSubject).filter(
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.classroom_id == classroom_id,
            TeacherSubject.subject_id == subject_id,
            TeacherSubject.academic_sessions_id == session_id
        ).first()
    
    def get_by_teacher(self, teacher_id: str, session_id: int) -> List[TeacherSubject]:
        return self.db.query(TeacherSubject).filter(
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.academic_sessions_id == session_id,
            TeacherSubject.is_active == True
        ).all()
    
    def get_by_class(self, classroom_id: int, session_id: int) -> List[TeacherSubject]:
        return self.db.query(TeacherSubject).filter(
            TeacherSubject.classroom_id == classroom_id,
            TeacherSubject.academic_sessions_id == session_id,
            TeacherSubject.is_active == True
        ).all()


class StudentClassRepository(BaseRepository[StudentClass]):
    """Student class repository."""
    
    def __init__(self, db: Session):
        super().__init__(StudentClass, db)
    
    def get_by_student_session(self, student_id: str, session_id: int) -> Optional[StudentClass]:
        return self.db.query(StudentClass).filter(
            StudentClass.student_id == student_id,
            StudentClass.academic_sessions_id == session_id
        ).first()
    
    def get_students_by_class(self, classroom_id: int, session_id: int) -> List[StudentClass]:
        return self.db.query(StudentClass).filter(
            StudentClass.classroom_id == classroom_id,
            StudentClass.academic_sessions_id == session_id,
            StudentClass.status == "ACTIVE"
        ).order_by(StudentClass.roll_number).all()
    
    def get_active_students_by_class(self, classroom_id: int, session_id: int) -> List[StudentClass]:
        return self.get_students_by_class(classroom_id, session_id)