# ============================================================
# repositories/academic_repositories.py - Academic & Other Repositories
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.model import (
    Assignment, AssignmentResult, StudyMaterial,
    Exam, ExamResult, Fee, Notice, ChatRoom, ChatMessage,
    StudentPromotionHistory
)
from app.repositories.base_repository import BaseRepository
from app.core.enums import AssignmentStatus, ExamStatus, FeeStatus


class AssignmentRepository(BaseRepository[Assignment]):
    """Assignment repository."""
    
    def __init__(self, db: Session):
        super().__init__(Assignment, db)
    
    def get_by_assignment_id(self, assignment_id: str) -> Optional[Assignment]:
        return self.db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    
    def get_by_teacher(self, teacher_id: str) -> List[Assignment]:
        return self.db.query(Assignment).filter(
            Assignment.teacher_subject_id == teacher_id
        ).order_by(Assignment.created_at.desc()).all()
    
    def get_by_classroom(self, classroom_id: int) -> List[Assignment]:
        return self.db.query(Assignment).filter(
            Assignment.classroom_id == classroom_id
        ).order_by(Assignment.created_at.desc()).all()
    
    def get_upcoming_assignments(self, classroom_id: int, days: int = 7) -> List[Assignment]:
        today = date.today()
        end_date = today + timedelta(days=days)
        return self.db.query(Assignment).filter(
            Assignment.classroom_id == classroom_id,
            Assignment.due_date >= today,
            Assignment.due_date <= end_date,
            Assignment.status.in_([AssignmentStatus.PUBLISHED, AssignmentStatus.DRAFT])
        ).order_by(Assignment.due_date).all()
    
    def get_pending_assignments(self, teacher_id: str) -> List[Assignment]:
        return self.db.query(Assignment).filter(
            Assignment.teacher_subject_id == teacher_id,
            Assignment.status == AssignmentStatus.DRAFT
        ).all()
    
    def update_statistics(self, assignment_id: int) -> Optional[Assignment]:
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
        return self.db.query(AssignmentResult).filter(
            AssignmentResult.assignment_id == assignment_id
        ).all()
    
    def get_by_student(self, student_class_id: int) -> List[AssignmentResult]:
        return self.db.query(AssignmentResult).filter(
            AssignmentResult.student_class_id == student_class_id
        ).all()
    
    def get_by_assignment_student(self, assignment_id: int, student_class_id: int) -> Optional[AssignmentResult]:
        return self.db.query(AssignmentResult).filter(
            AssignmentResult.assignment_id == assignment_id,
            AssignmentResult.student_class_id == student_class_id
        ).first()
    
    def get_or_create(self, assignment_id: int, student_class_id: int) -> AssignmentResult:
        result = self.get_by_assignment_student(assignment_id, student_class_id)
        if not result:
            result = AssignmentResult(assignment_id=assignment_id, student_class_id=student_class_id)
            self.db.add(result)
            self.db.flush()
        return result
    
    def get_assignment_stats(self, assignment_id: int) -> Dict[str, Any]:
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
            avg_marks = max_marks = min_marks = 0
        
        return {
            "total_students": total,
            "checked_students": checked,
            "unchecked_students": unchecked,
            "average_marks": round(avg_marks, 2),
            "max_marks": round(max_marks, 2),
            "min_marks": round(min_marks, 2)
        }


class StudyMaterialRepository(BaseRepository[StudyMaterial]):
    """Study material repository."""
    
    def __init__(self, db: Session):
        super().__init__(StudyMaterial, db)
    
    def get_by_material_id(self, material_id: str) -> Optional[StudyMaterial]:
        return self.db.query(StudyMaterial).filter(StudyMaterial.material_id == material_id).first()
    
    def get_by_class_subject(self, class_subject_id: int) -> List[StudyMaterial]:
        return self.db.query(StudyMaterial).filter(
            StudyMaterial.class_subject_id == class_subject_id,
            StudyMaterial.is_active == True
        ).order_by(StudyMaterial.created_at.desc()).all()
    
    def increment_download(self, material_id: int) -> Optional[StudyMaterial]:
        material = self.get_by_id(material_id)
        if material:
            material.download_count += 1
            self.db.flush()
        return material


class ExamRepository(BaseRepository[Exam]):
    """Exam repository."""
    
    def __init__(self, db: Session):
        super().__init__(Exam, db)
    
    def get_by_exam_id(self, exam_id: str) -> Optional[Exam]:
        return self.db.query(Exam).filter(Exam.exam_id == exam_id).first()
    
    def get_by_teacher(self, teacher_id: str) -> List[Exam]:
        return self.db.query(Exam).filter(
            Exam.teacher_subject_id == teacher_id
        ).order_by(Exam.exam_date.desc()).all()
    
    def get_by_classroom(self, classroom_id: int) -> List[Exam]:
        return self.db.query(Exam).filter(
            Exam.classroom_id == classroom_id
        ).order_by(Exam.exam_date.desc()).all()
    
    def get_upcoming_exams(self, classroom_id: int, days: int = 30) -> List[Exam]:
        today = date.today()
        end_date = today + timedelta(days=days)
        return self.db.query(Exam).filter(
            Exam.classroom_id == classroom_id,
            Exam.exam_date >= today,
            Exam.exam_date <= end_date,
            Exam.status.in_([ExamStatus.PUBLISHED, ExamStatus.DRAFT])
        ).order_by(Exam.exam_date).all()
    
    def get_results_pending(self, teacher_id: str) -> List[Exam]:
        return self.db.query(Exam).filter(
            Exam.teacher_subject_id == teacher_id,
            Exam.status == ExamStatus.COMPLETED,
            Exam.result_uploaded < Exam.total_students
        ).all()


class ExamResultRepository(BaseRepository[ExamResult]):
    """Exam result repository."""
    
    def __init__(self, db: Session):
        super().__init__(ExamResult, db)
    
    def get_by_exam(self, exam_id: int) -> List[ExamResult]:
        return self.db.query(ExamResult).filter(
            ExamResult.exam_id == exam_id
        ).order_by(ExamResult.rank_in_class).all()
    
    def get_by_student(self, student_class_id: int) -> List[ExamResult]:
        return self.db.query(ExamResult).filter(
            ExamResult.student_class_id == student_class_id
        ).all()
    
    def get_by_exam_student(self, exam_id: int, student_class_id: int) -> Optional[ExamResult]:
        return self.db.query(ExamResult).filter(
            ExamResult.exam_id == exam_id,
            ExamResult.student_class_id == student_class_id
        ).first()
    
    def get_or_create(self, exam_id: int, student_class_id: int) -> ExamResult:
        result = self.get_by_exam_student(exam_id, student_class_id)
        if not result:
            result = ExamResult(exam_id=exam_id, student_class_id=student_class_id)
            self.db.add(result)
            self.db.flush()
        return result
    
    def update_rankings(self, exam_id: int) -> None:
        results = self.get_by_exam(exam_id)
        sorted_results = sorted(
            [r for r in results if not r.is_absent],
            key=lambda r: r.obtained_marks,
            reverse=True
        )
        for idx, result in enumerate(sorted_results, 1):
            result.rank_in_class = idx
        self.db.flush()
    
    def get_exam_stats(self, exam_id: int) -> Dict[str, Any]:
        results = self.get_by_exam(exam_id)
        total = len(results)
        absent = sum(1 for r in results if r.is_absent)
        present = total - absent
        
        if present > 0:
            marks = [r.obtained_marks for r in results if not r.is_absent]
            avg_marks = sum(marks) / len(marks) if marks else 0
            max_marks = max(marks) if marks else 0
            min_marks = min(marks) if marks else 0
            pass_count = sum(1 for r in results if not r.is_absent and r.percentage >= 40)
        else:
            avg_marks = max_marks = min_marks = pass_count = 0
        
        return {
            "total_students": total,
            "present_students": present,
            "absent_students": absent,
            "average_marks": round(avg_marks, 2),
            "max_marks": round(max_marks, 2),
            "min_marks": round(min_marks, 2),
            "pass_count": pass_count,
            "pass_percentage": round((pass_count / present * 100), 2) if present > 0 else 0
        }


class FeeRepository(BaseRepository[Fee]):
    """Fee repository."""
    
    def __init__(self, db: Session):
        super().__init__(Fee, db)
    
    def get_by_fee_id(self, fee_id: str) -> Optional[Fee]:
        return self.db.query(Fee).filter(Fee.fee_id == fee_id).first()
    
    def get_by_student_class(self, student_class_id: int) -> List[Fee]:
        return self.db.query(Fee).filter(
            Fee.student_class_id == student_class_id
        ).order_by(Fee.fee_year.desc(), Fee.fee_month.desc()).all()
    
    def get_by_student_month(self, student_class_id: int, month: int, year: int) -> Optional[Fee]:
        return self.db.query(Fee).filter(
            Fee.student_class_id == student_class_id,
            Fee.fee_month == month,
            Fee.fee_year == year
        ).first()
    
    def get_overdue_fees(self) -> List[Fee]:
        today = date.today()
        return self.db.query(Fee).filter(
            Fee.due_date < today,
            Fee.status == FeeStatus.PENDING
        ).all()
    
    def get_student_summary(self, student_class_id: int) -> Dict[str, Any]:
        fees = self.get_by_student_class(student_class_id)
        total = sum(f.total_amount for f in fees)
        paid = sum(f.paid_amount for f in fees)
        discount = sum(f.discount_amount for f in fees)
        fine = sum(f.fine_amount for f in fees)
        pending = total - paid
        
        return {
            "total_amount": float(total),
            "paid_amount": float(paid),
            "pending_amount": float(pending),
            "discount_amount": float(discount),
            "fine_amount": float(fine),
            "status": FeeStatus.PAID if pending == 0 else FeeStatus.PENDING
        }
    
    def update_status(self, fee_id: int) -> Optional[Fee]:
        fee = self.get_by_id(fee_id)
        if fee:
            total_due = fee.total_amount + fee.fine_amount - fee.discount_amount
            if fee.paid_amount >= total_due:
                fee.status = FeeStatus.PAID
            elif fee.paid_amount > 0:
                fee.status = FeeStatus.PENDING
            else:
                fee.status = FeeStatus.PENDING
            
            if fee.status == FeeStatus.PENDING and fee.due_date < date.today():
                fee.status = FeeStatus.OVERDUE
            self.db.flush()
        return fee


class NoticeRepository(BaseRepository[Notice]):
    """Notice repository."""
    
    def __init__(self, db: Session):
        super().__init__(Notice, db)
    
    def get_by_notice_id(self, notice_id: str) -> Optional[Notice]:
        return self.db.query(Notice).filter(Notice.notice_id == notice_id).first()
    
    def get_active_notices(self) -> List[Notice]:
        today = date.today()
        return self.db.query(Notice).filter(
            Notice.is_active == True,
            Notice.publish_date <= today,
            or_(Notice.expiry_date >= today, Notice.expiry_date == None)
        ).order_by(Notice.is_pinned.desc(), Notice.publish_date.desc()).all()
    
    def get_user_notices(self, role: str, classroom_id: Optional[int] = None) -> List[Notice]:
        today = date.today()
        query = self.db.query(Notice).filter(
            Notice.is_active == True,
            Notice.publish_date <= today,
            or_(Notice.expiry_date >= today, Notice.expiry_date == None)
        )
        
        if role == "student":
            query = query.filter(Notice.audience.in_(['All', 'Student']))
        elif role == "teacher":
            query = query.filter(Notice.audience.in_(['All', 'Teacher']))
        elif role == "admin":
            query = query.filter(Notice.audience.in_(['All', 'Admin']))
        
        if classroom_id:
            query = query.filter(or_(Notice.classroom_id == classroom_id, Notice.classroom_id == None))
        
        return query.order_by(Notice.is_pinned.desc(), Notice.publish_date.desc()).all()


class ChatRoomRepository(BaseRepository[ChatRoom]):
    """Chat room repository."""
    
    def __init__(self, db: Session):
        super().__init__(ChatRoom, db)
    
    def get_by_student_teacher(self, student_class_id: int, teacher_subject_id: int) -> Optional[ChatRoom]:
        return self.db.query(ChatRoom).filter(
            ChatRoom.student_class_id == student_class_id,
            ChatRoom.teacher_subject_id == teacher_subject_id
        ).first()
    
    def get_rooms_by_teacher(self, teacher_id: str) -> List[ChatRoom]:
        return self.db.query(ChatRoom).filter(
            ChatRoom.teacher_subject_id == teacher_id,
            ChatRoom.is_active == True
        ).all()
    
    def get_rooms_by_student(self, student_class_id: int) -> List[ChatRoom]:
        return self.db.query(ChatRoom).filter(
            ChatRoom.student_class_id == student_class_id,
            ChatRoom.is_active == True
        ).all()


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Chat message repository."""
    
    def __init__(self, db: Session):
        super().__init__(ChatMessage, db)
    
    def get_by_room(self, room_id: int, limit: int = 50, before: Optional[datetime] = None) -> List[ChatMessage]:
        query = self.db.query(ChatMessage).filter(ChatMessage.chat_room_id == room_id)
        if before:
            query = query.filter(ChatMessage.created_at < before)
        return query.order_by(ChatMessage.created_at.desc()).limit(limit).all()


class StudentPromotionHistoryRepository(BaseRepository[StudentPromotionHistory]):
    """Student promotion history repository."""
    
    def __init__(self, db: Session):
        super().__init__(StudentPromotionHistory, db)
    
    def get_by_student(self, student_id: str) -> List[StudentPromotionHistory]:
        return self.db.query(StudentPromotionHistory).filter(
            StudentPromotionHistory.student_id == student_id
        ).order_by(StudentPromotionHistory.promotion_date.desc()).all()
