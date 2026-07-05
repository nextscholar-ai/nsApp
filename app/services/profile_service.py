# ============================================================
# services/profile_service.py - Profile Service
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.model import StudentProfile, TeacherProfile, AdminProfile
from app.repositories.profile_repository import (
    StudentProfileRepository,
    TeacherProfileRepository,
    AdminProfileRepository
)
from app.repositories.user_repository import UserRepository
from app.services.base_service import BaseService
from app.core.enums import UserRole

logger = logging.getLogger(__name__)


class StudentProfileService(BaseService[StudentProfile, StudentProfileRepository]):
    """Student profile service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.student_repo = StudentProfileRepository(db)
        self.user_repo = UserRepository(db)
        super().__init__(self.student_repo)
    
    def create_student_profile(
        self,
        user_id: int,
        student_id: str,
        student_name: str,
        **kwargs
    ) -> Optional[StudentProfile]:
        """
        Create a student profile.
        """
        # Check if profile exists
        if self.student_repo.get_by_user_id(user_id):
            return None
        
        if self.student_repo.get_by_student_id(student_id):
            return None
        
        # Create profile
        profile = self.student_repo.create(
            user_id=user_id,
            student_id=student_id,
            student_name=student_name,
            **kwargs
        )
        
        # Update user's student_id
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.student_id = student_id
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def get_student_by_id(self, student_id: str) -> Optional[StudentProfile]:
        """Get student profile by student ID."""
        return self.student_repo.get_by_student_id(student_id)
    
    def get_student_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        """Get student profile by user ID."""
        return self.student_repo.get_by_user_id(user_id)
    
    def get_students_by_class(self, classroom_id: int, session_id: int) -> List[StudentProfile]:
        """Get students in a class."""
        return self.student_repo.get_students_by_class(classroom_id, session_id)
    
    def search_students(self, search: str, is_active: Optional[bool] = None) -> List[StudentProfile]:
        """Search students."""
        return self.student_repo.search_students(search, is_active)
    
    def update_student_profile(self, student_id: str, **kwargs) -> Optional[StudentProfile]:
        """Update student profile."""
        profile = self.student_repo.get_by_student_id(student_id)
        if profile:
            return self.student_repo.update(profile, **kwargs)
        return None
    
    def get_student_with_user(self, student_id: str) -> Dict[str, Any]:
        """Get student with user details."""
        profile = self.student_repo.get_by_student_id(student_id)
        if not profile:
            return {"profile": None}
        
        return {
            "profile": profile,
            "user": self.user_repo.get_by_id(profile.user_id)
        }


class TeacherProfileService(BaseService[TeacherProfile, TeacherProfileRepository]):
    """Teacher profile service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.teacher_repo = TeacherProfileRepository(db)
        self.user_repo = UserRepository(db)
        super().__init__(self.teacher_repo)
    
    def create_teacher_profile(
        self,
        user_id: int,
        teacher_id: str,
        teacher_name: str,
        **kwargs
    ) -> Optional[TeacherProfile]:
        """Create a teacher profile."""
        if self.teacher_repo.get_by_user_id(user_id):
            return None
        
        if self.teacher_repo.get_by_teacher_id(teacher_id):
            return None
        
        profile = self.teacher_repo.create(
            user_id=user_id,
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            **kwargs
        )
        
        # Update user's teacher_id
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.teacher_id = teacher_id
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def get_teacher_by_id(self, teacher_id: str) -> Optional[TeacherProfile]:
        """Get teacher profile by teacher ID."""
        return self.teacher_repo.get_by_teacher_id(teacher_id)
    
    def get_teacher_by_user_id(self, user_id: int) -> Optional[TeacherProfile]:
        """Get teacher profile by user ID."""
        return self.teacher_repo.get_by_user_id(user_id)
    
    def search_teachers(self, search: str, **filters) -> List[TeacherProfile]:
        """Search teachers."""
        return self.teacher_repo.search_teachers(search, **filters)
    
    def update_teacher_profile(self, teacher_id: str, **kwargs) -> Optional[TeacherProfile]:
        """Update teacher profile."""
        profile = self.teacher_repo.get_by_teacher_id(teacher_id)
        if profile:
            return self.teacher_repo.update(profile, **kwargs)
        return None


class AdminProfileService(BaseService[AdminProfile, AdminProfileRepository]):
    """Admin profile service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.admin_repo = AdminProfileRepository(db)
        self.user_repo = UserRepository(db)
        super().__init__(self.admin_repo)
    
    def create_admin_profile(
        self,
        user_id: int,
        admin_id: str,
        admin_name: str,
        **kwargs
    ) -> Optional[AdminProfile]:
        """Create an admin profile."""
        if self.admin_repo.get_by_user_id(user_id):
            return None
        
        if self.admin_repo.get_by_admin_id(admin_id):
            return None
        
        profile = self.admin_repo.create(
            user_id=user_id,
            admin_id=admin_id,
            admin_name=admin_name,
            **kwargs
        )
        
        # Update user's admin_id
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.admin_id = admin_id
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def get_admin_by_id(self, admin_id: str) -> Optional[AdminProfile]:
        """Get admin profile by admin ID."""
        return self.admin_repo.get_by_admin_id(admin_id)
    
    def get_admin_by_user_id(self, user_id: int) -> Optional[AdminProfile]:
        """Get admin profile by user ID."""
        return self.admin_repo.get_by_user_id(user_id)
    
    def get_super_admins(self) -> List[AdminProfile]:
        """Get super admins."""
        return self.admin_repo.get_super_admins()
    
    def update_admin_profile(self, admin_id: str, **kwargs) -> Optional[AdminProfile]:
        """Update admin profile."""
        profile = self.admin_repo.get_by_admin_id(admin_id)
        if profile:
            return self.admin_repo.update(profile, **kwargs)
        return None