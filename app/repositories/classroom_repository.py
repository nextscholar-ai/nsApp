# ============================================================
# repositories/classroom_repository.py - Classroom Repository
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.model import ClassRoom, ClassSubject, Subject
from app.repositories.base_repository import BaseRepository


class ClassRoomRepository(BaseRepository[ClassRoom]):
    """Classroom repository."""
    
    def __init__(self, db: Session):
        super().__init__(ClassRoom, db)
    
    def get_by_code(self, code: str, session_id: int) -> Optional[ClassRoom]:
        """Get classroom by code and session."""
        return self.db.query(ClassRoom).filter(
            ClassRoom.class_code == code,
            ClassRoom.academic_sessions_id == session_id
        ).first()
    
    def get_by_display_name(self, display_name: str, session_id: int) -> Optional[ClassRoom]:
        """Get classroom by display name."""
        return self.db.query(ClassRoom).filter(
            ClassRoom.display_name == display_name,
            ClassRoom.academic_sessions_id == session_id
        ).first()
    
    def get_classes_by_session(self, session_id: int) -> List[ClassRoom]:
        """Get all classes for a session."""
        return self.db.query(ClassRoom).filter(
            ClassRoom.academic_sessions_id == session_id,
            ClassRoom.is_active == True
        ).order_by(ClassRoom.class_name, ClassRoom.section).all()
    
    def get_classes_by_teacher(self, teacher_id: str, session_id: int) -> List[ClassRoom]:
        """Get classes taught by a teacher."""
        from app.model import TeacherSubject
        
        return self.db.query(ClassRoom).join(
            TeacherSubject,
            TeacherSubject.classroom_id == ClassRoom.id
        ).filter(
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.academic_sessions_id == session_id,
            ClassRoom.is_active == True
        ).distinct().all()
    
    def get_classes_with_teacher(self, session_id: int) -> List[Dict[str, Any]]:
        """Get classes with their class teachers."""
        classes = self.get_classes_by_session(session_id)
        result = []
        for cls in classes:
            result.append({
                "class": cls,
                "class_teacher": cls.class_teacher
            })
        return result
    
    def get_class_subjects(self, class_id: int) -> List[Dict[str, Any]]:
        """Get subjects assigned to a class."""
        class_subjects = self.db.query(ClassSubject).filter(
            ClassSubject.classroom_id == class_id,
            ClassSubject.is_active == True
        ).order_by(ClassSubject.display_order).all()
        
        result = []
        for cs in class_subjects:
            result.append({
                "class_subject": cs,
                "subject": cs.subject,
                "teachers": cs.teacher_subjects if cs.teacher_subjects else []
            })
        return result


class SubjectRepository(BaseRepository[Subject]):
    """Subject repository."""
    
    def __init__(self, db: Session):
        super().__init__(Subject, db)
    
    def get_by_code(self, code: str) -> Optional[Subject]:
        """Get subject by code."""
        return self.db.query(Subject).filter(Subject.subject_code == code).first()
    
    def get_by_name(self, name: str) -> Optional[Subject]:
        """Get subject by name."""
        return self.db.query(Subject).filter(Subject.subject_name == name).first()
    
    def get_active_subjects(self) -> List[Subject]:
        """Get all active subjects."""
        return self.db.query(Subject).filter(
            Subject.is_active == True
        ).order_by(Subject.display_order).all()
    
    def get_subjects_by_type(self, subject_type: str) -> List[Subject]:
        """Get subjects by type."""
        return self.db.query(Subject).filter(
            Subject.subject_type == subject_type,
            Subject.is_active == True
        ).all()