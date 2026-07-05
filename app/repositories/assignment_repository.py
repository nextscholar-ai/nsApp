# ============================================================
# repositories/assignment_repository.py - Assignment Repository
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, datetime

from app.model import Assignment, AssignmentResult
from app.repositories.base_repository import BaseRepository
from app.core.enums import AssignmentStatus


class AssignmentRepository(BaseRepository[Assignment]):
    """Assignment repository."""
    
    def __init__(self, db: Session):
        super().__init__(Assignment, db)
    
    def get_by_assignment_id(self, assignment_id: str) -> Optional[Assignment]:
        """Get assignment by ID."""
        return self.db.query(Assignment).filter(
            Assignment.assignment_id == assignment_id
        ).first()
    
    def get_by_teacher(self, teacher_id: str) -> List[Assignment]:
        """Get assignments by teacher."""
        return self.db.query(Assignment).filter(
            Assignment.teacher_subject_id == teacher_id
        ).order_by(Assignment.created_at.desc()).all()
    
    def get_by_classroom(self, classroom_id: int) -> List[Assignment]:
        """Get assignments by classroom."""
        return self.db.query(Assignment).filter(
            Assignment.classroom_id == classroom_id
        ).order_by(Assignment.created_at.desc()).all()
    
    def get_by_classroom_teacher(self, classroom_id: int, teacher_id: str) -> List[Assignment]:
        """Get assignments by classroom and teacher."""
        return self.db.query(Assignment).filter(
            Assignment.classroom_id == classroom_id,
            Assignment.teacher_subject_id == teacher_id
        ).order_by(Assignment.created_at.desc()).all()
    
    def get_upcoming_assignments(self, classroom_id: int, days: int = 7) -> List[Assignment]:
        """Get upcoming assignments for a classroom."""
        today = date.today()
        end_date = today + timedelta(days=days)
        
        return self.db.query(Assignment).filter(
            Assignment.classroom_id == classroom_id,
            Assignment.due_date >= today,
            Assignment.due_date <= end_date,
            Assignment.status.in_([AssignmentStatus.PUBLISHED, AssignmentStatus.DRAFT])
        ).order_by(Assignment.due_date).all()
    
    def get_pending_assignments(self, teacher_id: str) -> List[Assignment]:
        """Get pending assignments for a teacher."""
        return self.db.query(Assignment).filter(
            Assignment.teacher_subject_id == teacher_id,
            Assignment.status == AssignmentStatus.DRAFT
        ).all()
    
    def get_overdue_assignments(self) -> List[Assignment]:
        """Get overdue assignments."""
        today = date.today()
        return self.db.query(Assignment).filter(
            Assignment.due_date < today,
            Assignment.status.in_([AssignmentStatus.PUBLISHED, AssignmentStatus.DRAFT])
        ).all()
    
    def update_statistics(self, assignment_id: int) -> Assignment:
        """Update assignment statistics."""
        assignment = self.get_by_id(assignment_id)
        if assignment:
            results = self.db.query(AssignmentResult).filter(
                AssignmentResult.assignment_id == assignment_id
            ).all()
            
            assignment.total_students = len(results)
            assignment.checked_students = sum(1 for r in results if r.is_checked)
            self.db.flush()
        return assignment


class AssignmentResultRepository(BaseRepository[AssignmentResult]):
    """Assignment result repository."""
    
    def __init__(self, db: Session):
        super().__init__(AssignmentResult, db)
    
    def get_by_assignment(self, assignment_id: int) -> List[AssignmentResult]:
        """Get results by assignment."""
        return self.db.query(AssignmentResult).filter(
            AssignmentResult.assignment_id == assignment_id
        ).all()
    
    def get_by_student(self, student_class_id: int) -> List[AssignmentResult]:
        """Get results by student class."""
        return self.db.query(AssignmentResult).filter(
            AssignmentResult.student_class_id == student_class_id
        ).all()
    
    def get_by_assignment_student(self, assignment_id: int, student_class_id: int) -> Optional[AssignmentResult]:
        """Get result by assignment and student."""
        return self.db.query(AssignmentResult).filter(
            AssignmentResult.assignment_id == assignment_id,
            AssignmentResult.student_class_id == student_class_id
        ).first()
    
    def get_or_create(self, assignment_id: int, student_class_id: int) -> AssignmentResult:
        """Get or create assignment result."""
        result = self.get_by_assignment_student(assignment_id, student_class_id)
        if not result:
            result = AssignmentResult(
                assignment_id=assignment_id,
                student_class_id=student_class_id
            )
            self.db.add(result)
            self.db.flush()
        return result
    
    def get_assignment_stats(self, assignment_id: int) -> Dict[str, Any]:
        """Get statistics for an assignment."""
        results = self.get_by_assignment(assignment_id)
        
        total = len(results)
        checked = sum(1 for r in results if r.is_checked)
        unchecked = total - checked
        
        if checked > 0:
            marks = [r.obtained_marks for r in results if r.is_checked]
            avg_marks = sum(marks) / len(marks) if marks else 0
            max_marks = max(marks) if marks else 0
            min_marks = min(marks) if marks else 0
        else:
            avg_marks = 0
            max_marks = 0
            min_marks = 0
        
        return {
            "total_students": total,
            "checked_students": checked,
            "unchecked_students": unchecked,
            "average_marks": round(avg_marks, 2),
            "max_marks": round(max_marks, 2),
            "min_marks": round(min_marks, 2)
        }