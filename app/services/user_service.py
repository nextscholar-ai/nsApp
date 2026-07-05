# ============================================================
# services/user_service.py - User & Profile Service
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.model import User, StudentProfile, TeacherProfile, AdminProfile, AcademicSession, ClassRoom, Subject, ClassSubject, TeacherSubject, StudentClass
from app.repositories.core_repositories import (
    UserRepository, StudentProfileRepository, TeacherProfileRepository, AdminProfileRepository,
    AcademicSessionRepository, ClassRoomRepository, SubjectRepository, ClassSubjectRepository,
    TeacherSubjectRepository, StudentClassRepository
)
from app.auth import hash_password
from app.core.enums import UserRole

logger = logging.getLogger(__name__)


class userService:
    """User management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.student_repo = StudentProfileRepository(db)
        self.teacher_repo = TeacherProfileRepository(db)
        self.admin_repo = AdminProfileRepository(db)
        self.session_repo = AcademicSessionRepository(db)
        self.classroom_repo = ClassRoomRepository(db)
        self.subject_repo = SubjectRepository(db)
        self.class_subject_repo = ClassSubjectRepository(db)
        self.teacher_subject_repo = TeacherSubjectRepository(db)
        self.student_class_repo = StudentClassRepository(db)
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, email: str, phone: str, password: str, role: UserRole, **kwargs) -> Optional[User]:
        if self.user_repo.get_by_email(email) or self.user_repo.get_by_phone(phone):
            return None
        user = self.user_repo.create(
            email=email.lower().strip(),
            phone=phone.strip(),
            role=role,
            password_hash=hash_password(password),
            **kwargs
        )
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.user_repo.get_by_email(email)
    
    def get_user_by_role(self, role: UserRole) -> List[User]:
        return self.user_repo.get_user_by_role(role)
    
    def search_user(self, search: str, **filters) -> List[User]:
        return self.user_repo.search_user(search, **filters)
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        return self.user_repo.update_by_id(user_id, **kwargs)
    
    def delete_user(self, user_id: int, soft_delete: bool = True) -> bool:
        return self.user_repo.delete_by_id(user_id, soft_delete)
    
    def activate_user(self, user_id: int) -> Optional[User]:
        return self.user_repo.update_by_id(user_id, is_active=True)
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        return self.user_repo.update_by_id(user_id, is_active=False)
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        return self.user_repo.get_dashboard_stats()
    
    # ==================== STUDENT PROFILE ====================
    
    def create_student_profile(self, user_id: int, student_id: str, student_name: str, **kwargs) -> Optional[StudentProfile]:
        if self.student_repo.get_by_user_id(user_id) or self.student_repo.get_by_student_id(student_id):
            return None
        profile = self.student_repo.create(user_id=user_id, student_id=student_id, student_name=student_name, **kwargs)
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.student_id = student_id
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def get_student(self, student_id: str) -> Optional[StudentProfile]:
        return self.student_repo.get_by_student_id(student_id)
    
    def get_student_by_user(self, user_id: int) -> Optional[StudentProfile]:
        return self.student_repo.get_by_user_id(user_id)
    
    def get_students_by_class(self, classroom_id: int, session_id: int) -> List[StudentProfile]:
        return self.student_repo.get_students_by_class(classroom_id, session_id)
    
    def search_students(self, search: str, is_active: Optional[bool] = None) -> List[StudentProfile]:
        return self.student_repo.search_students(search, is_active)
    
    def update_student(self, student_id: str, **kwargs) -> Optional[StudentProfile]:
        profile = self.student_repo.get_by_student_id(student_id)
        if profile:
            return self.student_repo.update(profile, **kwargs)
        return None
    
    # ==================== TEACHER PROFILE ====================
    
    def create_teacher_profile(self, user_id: int, teacher_id: str, teacher_name: str, **kwargs) -> Optional[TeacherProfile]:
        if self.teacher_repo.get_by_user_id(user_id) or self.teacher_repo.get_by_teacher_id(teacher_id):
            return None
        profile = self.teacher_repo.create(user_id=user_id, teacher_id=teacher_id, teacher_name=teacher_name, **kwargs)
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.teacher_id = teacher_id
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def get_teacher(self, teacher_id: str) -> Optional[TeacherProfile]:
        return self.teacher_repo.get_by_teacher_id(teacher_id)
    
    def get_teacher_by_user(self, user_id: int) -> Optional[TeacherProfile]:
        return self.teacher_repo.get_by_user_id(user_id)
    
    def search_teachers(self, search: str, **filters) -> List[TeacherProfile]:
        return self.teacher_repo.search_teachers(search, **filters)
    
    def update_teacher(self, teacher_id: str, **kwargs) -> Optional[TeacherProfile]:
        profile = self.teacher_repo.get_by_teacher_id(teacher_id)
        if profile:
            return self.teacher_repo.update(profile, **kwargs)
        return None
    
    # ==================== ADMIN PROFILE ====================
    
    def create_admin_profile(self, user_id: int, admin_id: str, admin_name: str, **kwargs) -> Optional[AdminProfile]:
        if self.admin_repo.get_by_user_id(user_id) or self.admin_repo.get_by_admin_id(admin_id):
            return None
        profile = self.admin_repo.create(user_id=user_id, admin_id=admin_id, admin_name=admin_name, **kwargs)
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.admin_id = admin_id
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def get_admin(self, admin_id: str) -> Optional[AdminProfile]:
        return self.admin_repo.get_by_admin_id(admin_id)
    
    def get_admin_by_user(self, user_id: int) -> Optional[AdminProfile]:
        return self.admin_repo.get_by_user_id(user_id)
    
    def get_super_admins(self) -> List[AdminProfile]:
        return self.admin_repo.get_super_admins()
    
    def update_admin(self, admin_id: str, **kwargs) -> Optional[AdminProfile]:
        profile = self.admin_repo.get_by_admin_id(admin_id)
        if profile:
            return self.admin_repo.update(profile, **kwargs)
        return None
    
    # ==================== ACADEMIC SESSION ====================
    
    def create_session(self, **kwargs) -> AcademicSession:
        return self.session_repo.create(**kwargs)
    
    def get_current_session(self) -> Optional[AcademicSession]:
        return self.session_repo.get_current_session()
    
    def get_all_sessions(self) -> List[AcademicSession]:
        return self.session_repo.get_active_sessions()
    
    def set_current_session(self, session_id: int) -> Optional[AcademicSession]:
        return self.session_repo.set_current_session(session_id)
    
    # ==================== CLASSROOM ====================
    
    def create_classroom(self, **kwargs) -> ClassRoom:
        return self.classroom_repo.create(**kwargs)
    
    def get_classroom(self, class_id: int) -> Optional[ClassRoom]:
        return self.classroom_repo.get_by_id(class_id)
    
    def get_classes_by_session(self, session_id: int) -> List[ClassRoom]:
        return self.classroom_repo.get_classes_by_session(session_id)
    
    def update_classroom(self, class_id: int, **kwargs) -> Optional[ClassRoom]:
        return self.classroom_repo.update_by_id(class_id, **kwargs)
    
    # ==================== SUBJECT ====================
    
    def create_subject(self, **kwargs) -> Subject:
        return self.subject_repo.create(**kwargs)
    
    def get_subject(self, subject_id: int) -> Optional[Subject]:
        return self.subject_repo.get_by_id(subject_id)
    
    def get_all_subjects(self) -> List[Subject]:
        return self.subject_repo.get_active_subjects()
    
    def update_subject(self, subject_id: int, **kwargs) -> Optional[Subject]:
        return self.subject_repo.update_by_id(subject_id, **kwargs)
    
    # ==================== CLASS SUBJECT ====================
    
    def assign_subject_to_class(self, **kwargs) -> ClassSubject:
        return self.class_subject_repo.create(**kwargs)
    
    def get_class_subjects(self, classroom_id: int, session_id: int) -> List[ClassSubject]:
        return self.class_subject_repo.get_subjects_by_class(classroom_id, session_id)
    
    # ==================== TEACHER SUBJECT ====================
    
    def assign_teacher_to_subject(self, **kwargs) -> TeacherSubject:
        return self.teacher_subject_repo.create(**kwargs)
    
    def get_teacher_subjects(self, teacher_id: str, session_id: int) -> List[TeacherSubject]:
        return self.teacher_subject_repo.get_by_teacher(teacher_id, session_id)
    
    # ==================== STUDENT CLASS ====================
    
    def enroll_student(self, **kwargs) -> StudentClass:
        return self.student_class_repo.create(**kwargs)
    
    def get_student_class(self, student_id: str, session_id: int) -> Optional[StudentClass]:
        return self.student_class_repo.get_by_student_session(student_id, session_id)
    
    def get_class_students(self, classroom_id: int, session_id: int) -> List[StudentClass]:
        return self.student_class_repo.get_students_by_class(classroom_id, session_id)