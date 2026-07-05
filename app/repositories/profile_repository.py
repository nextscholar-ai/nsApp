# ============================================================
# repositories/profile_repository.py - Profile Repository
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.model import StudentProfile, TeacherProfile, AdminProfile
from app.repositories.base_repository import BaseRepository
from app.core.enums import Gender


class StudentProfileRepository(BaseRepository[StudentProfile]):
    """Student profile repository."""
    
    def __init__(self, db: Session):
        super().__init__(StudentProfile, db)
    
    def get_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        """Get student profile by user ID."""
        return self.db.query(StudentProfile).filter(
            StudentProfile.user_id == user_id
        ).first()
    
    def get_by_student_id(self, student_id: str) -> Optional[StudentProfile]:
        """Get student profile by student ID."""
        return self.db.query(StudentProfile).filter(
            StudentProfile.student_id == student_id
        ).first()
    
    def get_by_admission_number(self, admission_number: str) -> Optional[StudentProfile]:
        """Get student profile by admission number."""
        return self.db.query(StudentProfile).filter(
            StudentProfile.admission_number == admission_number
        ).first()
    
    def search_students(
        self,
        search: str,
        is_active: Optional[bool] = None
    ) -> List[StudentProfile]:
        """Search students by name or student ID."""
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
        """Get students enrolled in a specific class."""
        from app.model import StudentClass
        
        return self.db.query(StudentProfile).join(
            StudentClass,
            StudentClass.student_id == StudentProfile.student_id
        ).filter(
            StudentClass.classroom_id == classroom_id,
            StudentClass.academic_sessions_id == session_id,
            StudentClass.status == "ACTIVE"
        ).all()
    
    def get_student_with_user(self, student_id: str) -> Optional[StudentProfile]:
        """Get student profile with user details."""
        return self.db.query(StudentProfile).filter(
            StudentProfile.student_id == student_id
        ).first()


class TeacherProfileRepository(BaseRepository[TeacherProfile]):
    """Teacher profile repository."""
    
    def __init__(self, db: Session):
        super().__init__(TeacherProfile, db)
    
    def get_by_user_id(self, user_id: int) -> Optional[TeacherProfile]:
        """Get teacher profile by user ID."""
        return self.db.query(TeacherProfile).filter(
            TeacherProfile.user_id == user_id
        ).first()
    
    def get_by_teacher_id(self, teacher_id: str) -> Optional[TeacherProfile]:
        """Get teacher profile by teacher ID."""
        return self.db.query(TeacherProfile).filter(
            TeacherProfile.teacher_id == teacher_id
        ).first()
    
    def get_by_employee_code(self, employee_code: str) -> Optional[TeacherProfile]:
        """Get teacher profile by employee code."""
        return self.db.query(TeacherProfile).filter(
            TeacherProfile.employee_code == employee_code
        ).first()
    
    def search_teachers(
        self,
        search: str,
        department: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[TeacherProfile]:
        """Search teachers by name or teacher ID."""
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
        """Get teachers assigned to a subject."""
        from app.model import TeacherSubject
        
        return self.db.query(TeacherProfile).join(
            TeacherSubject,
            TeacherSubject.teacher_id == TeacherProfile.teacher_id
        ).filter(
            TeacherSubject.subject_id == subject_id,
            TeacherSubject.academic_sessions_id == session_id
        ).all()


class AdminProfileRepository(BaseRepository[AdminProfile]):
    """Admin profile repository."""
    
    def __init__(self, db: Session):
        super().__init__(AdminProfile, db)
    
    def get_by_user_id(self, user_id: int) -> Optional[AdminProfile]:
        """Get admin profile by user ID."""
        return self.db.query(AdminProfile).filter(
            AdminProfile.user_id == user_id
        ).first()
    
    def get_by_admin_id(self, admin_id: str) -> Optional[AdminProfile]:
        """Get admin profile by admin ID."""
        return self.db.query(AdminProfile).filter(
            AdminProfile.admin_id == admin_id
        ).first()
    
    def get_super_admins(self) -> List[AdminProfile]:
        """Get all super admins."""
        return self.db.query(AdminProfile).filter(
            AdminProfile.super_admin == True,
            AdminProfile.is_active == True
        ).all()
    
    def get_admins_with_create_permission(self) -> List[AdminProfile]:
        """Get admins with create admin permission."""
        return self.db.query(AdminProfile).filter(
            AdminProfile.can_create_admin == True,
            AdminProfile.is_active == True
        ).all()