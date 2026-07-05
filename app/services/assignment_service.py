# ============================================================
# services/assignment_service.py - Complete Services
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging

from app.model import (
    Assignment, AssignmentResult, StudyMaterial,
    Exam, ExamResult, Fee, Notice, ChatRoom, ChatMessage,
    StudentPromotionHistory
)
from app.repositories.academic_repository import (
    AssignmentRepository, AssignmentResultRepository, StudyMaterialRepository,
    ExamRepository, ExamResultRepository, FeeRepository,
    NoticeRepository, ChatRoomRepository, ChatMessageRepository,
    StudentPromotionHistoryRepository
)
from app.repositories.core_repositories import StudentClassRepository, TeacherSubjectRepository
from app.core.enums import FeeStatus

logger = logging.getLogger(__name__)


class AssignmentService:
    """Assignment management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.result_repo = AssignmentResultRepository(db)
        self.student_class_repo = StudentClassRepository(db)
    
    def create_assignment(self, **kwargs) -> Assignment:
        return self.assignment_repo.create(**kwargs)
    
    def get_assignment(self, assignment_id: int) -> Optional[Assignment]:
        return self.assignment_repo.get_by_id(assignment_id)
    
    def get_assignments_by_teacher(self, teacher_id: str) -> List[Assignment]:
        return self.assignment_repo.get_by_teacher(teacher_id)
    
    def get_assignments_by_class(self, classroom_id: int) -> List[Assignment]:
        return self.assignment_repo.get_by_classroom(classroom_id)
    
    def get_upcoming_assignments(self, classroom_id: int, days: int = 7) -> List[Assignment]:
        return self.assignment_repo.get_upcoming_assignments(classroom_id, days)
    
    def update_assignment(self, assignment_id: int, **kwargs) -> Optional[Assignment]:
        return self.assignment_repo.update_by_id(assignment_id, **kwargs)
    
    def delete_assignment(self, assignment_id: int) -> bool:
        return self.assignment_repo.delete_by_id(assignment_id)
    
    def grade_assignment(self, assignment_id: int, results_data: List[Dict[str, Any]]) -> List[AssignmentResult]:
        graded = []
        for item in results_data:
            student_class_id = item.get("student_class_id")
            existing = self.result_repo.get_by_assignment_student(assignment_id, student_class_id)
            
            if existing:
                existing.obtained_marks = item.get("obtained_marks", 0)
                existing.percentage = item.get("percentage", 0)
                existing.grade = item.get("grade")
                existing.remarks = item.get("remarks")
                existing.is_checked = True
                existing.checked_at = datetime.utcnow()
                graded.append(existing)
            else:
                new_result = AssignmentResult(
                    assignment_id=assignment_id,
                    student_class_id=student_class_id,
                    obtained_marks=item.get("obtained_marks", 0),
                    percentage=item.get("percentage", 0),
                    grade=item.get("grade"),
                    remarks=item.get("remarks"),
                    is_checked=True,
                    checked_at=datetime.utcnow()
                )
                self.db.add(new_result)
                graded.append(new_result)
        
        self.db.flush()
        self.assignment_repo.update_statistics(assignment_id)
        return graded
    
    def get_assignment_results(self, assignment_id: int) -> List[AssignmentResult]:
        return self.result_repo.get_by_assignment(assignment_id)
    
    def get_student_assignments(self, student_class_id: int) -> List[AssignmentResult]:
        return self.result_repo.get_by_student(student_class_id)
    
    def get_assignment_stats(self, assignment_id: int) -> Dict[str, Any]:
        return self.result_repo.get_assignment_stats(assignment_id)


class ExamService:
    """Exam management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.exam_repo = ExamRepository(db)
        self.result_repo = ExamResultRepository(db)
        self.student_class_repo = StudentClassRepository(db)
    
    def create_exam(self, **kwargs) -> Exam:
        return self.exam_repo.create(**kwargs)
    
    def get_exam(self, exam_id: int) -> Optional[Exam]:
        return self.exam_repo.get_by_id(exam_id)
    
    def get_exams_by_teacher(self, teacher_id: str) -> List[Exam]:
        return self.exam_repo.get_by_teacher(teacher_id)
    
    def get_exams_by_class(self, classroom_id: int) -> List[Exam]:
        return self.exam_repo.get_by_classroom(classroom_id)
    
    def get_upcoming_exams(self, classroom_id: int, days: int = 30) -> List[Exam]:
        return self.exam_repo.get_upcoming_exams(classroom_id, days)
    
    def update_exam(self, exam_id: int, **kwargs) -> Optional[Exam]:
        return self.exam_repo.update_by_id(exam_id, **kwargs)
    
    def delete_exam(self, exam_id: int) -> bool:
        return self.exam_repo.delete_by_id(exam_id)
    
    def upload_exam_results(self, exam_id: int, results_data: List[Dict[str, Any]]) -> List[ExamResult]:
        uploaded = []
        for item in results_data:
            student_class_id = item.get("student_class_id")
            existing = self.result_repo.get_by_exam_student(exam_id, student_class_id)
            
            if existing:
                existing.obtained_marks = item.get("obtained_marks", 0)
                existing.percentage = item.get("percentage", 0)
                existing.grade = item.get("grade")
                existing.remarks = item.get("remarks")
                existing.rank_in_class = item.get("rank_in_class")
                existing.is_absent = item.get("is_absent", False)
                existing.checked_at = datetime.utcnow()
                uploaded.append(existing)
            else:
                new_result = ExamResult(
                    exam_id=exam_id,
                    student_class_id=student_class_id,
                    obtained_marks=item.get("obtained_marks", 0),
                    percentage=item.get("percentage", 0),
                    grade=item.get("grade"),
                    remarks=item.get("remarks"),
                    rank_in_class=item.get("rank_in_class"),
                    is_absent=item.get("is_absent", False),
                    checked_at=datetime.utcnow()
                )
                self.db.add(new_result)
                uploaded.append(new_result)
        
        self.db.flush()
        self.result_repo.update_rankings(exam_id)
        
        # Update exam statistics
        exam = self.exam_repo.get_by_id(exam_id)
        if exam:
            exam.result_uploaded = len(uploaded)
            self.db.flush()
        
        return uploaded
    
    def get_exam_results(self, exam_id: int) -> List[ExamResult]:
        return self.result_repo.get_by_exam(exam_id)
    
    def get_student_exams(self, student_class_id: int) -> List[ExamResult]:
        return self.result_repo.get_by_student(student_class_id)
    
    def get_exam_stats(self, exam_id: int) -> Dict[str, Any]:
        return self.result_repo.get_exam_stats(exam_id)


class FeeService:
    """Fee management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.fee_repo = FeeRepository(db)
    
    def create_fee(self, **kwargs) -> Fee:
        return self.fee_repo.create(**kwargs)
    
    def get_fee(self, fee_id: int) -> Optional[Fee]:
        return self.fee_repo.get_by_id(fee_id)
    
    def get_student_fees(self, student_class_id: int) -> List[Fee]:
        return self.fee_repo.get_by_student_class(student_class_id)
    
    def get_fee_by_month(self, student_class_id: int, month: int, year: int) -> Optional[Fee]:
        return self.fee_repo.get_by_student_month(student_class_id, month, year)
    
    def update_fee(self, fee_id: int, **kwargs) -> Optional[Fee]:
        fee = self.fee_repo.update_by_id(fee_id, **kwargs)
        if fee:
            self.fee_repo.update_status(fee_id)
        return fee
    
    def pay_fee(self, fee_id: int, amount: Decimal, payment_date: date) -> Optional[Fee]:
        fee = self.fee_repo.get_by_id(fee_id)
        if fee:
            fee.paid_amount += amount
            fee.paid_date = payment_date
            self.db.flush()
            self.fee_repo.update_status(fee_id)
        return fee
    
    def get_student_fee_summary(self, student_class_id: int) -> Dict[str, Any]:
        return self.fee_repo.get_student_summary(student_class_id)
    
    def get_overdue_fees(self) -> List[Fee]:
        return self.fee_repo.get_overdue_fees()


class NoticeService:
    """Notice management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notice_repo = NoticeRepository(db)
    
    def create_notice(self, **kwargs) -> Notice:
        return self.notice_repo.create(**kwargs)
    
    def get_notice(self, notice_id: int) -> Optional[Notice]:
        return self.notice_repo.get_by_id(notice_id)
    
    def get_active_notices(self) -> List[Notice]:
        return self.notice_repo.get_active_notices()
    
    def get_user_notices(self, role: str, classroom_id: Optional[int] = None) -> List[Notice]:
        return self.notice_repo.get_user_notices(role, classroom_id)
    
    def update_notice(self, notice_id: int, **kwargs) -> Optional[Notice]:
        return self.notice_repo.update_by_id(notice_id, **kwargs)
    
    def delete_notice(self, notice_id: int) -> bool:
        return self.notice_repo.delete_by_id(notice_id)
    
    def pin_notice(self, notice_id: int) -> Optional[Notice]:
        return self.notice_repo.update_by_id(notice_id, is_pinned=True)
    
    def unpin_notice(self, notice_id: int) -> Optional[Notice]:
        return self.notice_repo.update_by_id(notice_id, is_pinned=False)


class ChatService:
    """Chat management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.room_repo = ChatRoomRepository(db)
        self.message_repo = ChatMessageRepository(db)
    
    def create_room(self, **kwargs) -> ChatRoom:
        return self.room_repo.create(**kwargs)
    
    def get_room(self, room_id: int) -> Optional[ChatRoom]:
        return self.room_repo.get_by_id(room_id)
    
    def get_room_by_student_teacher(self, student_class_id: int, teacher_subject_id: int) -> Optional[ChatRoom]:
        return self.room_repo.get_by_student_teacher(student_class_id, teacher_subject_id)
    
    def get_teacher_rooms(self, teacher_id: str) -> List[ChatRoom]:
        return self.room_repo.get_rooms_by_teacher(teacher_id)
    
    def get_student_rooms(self, student_class_id: int) -> List[ChatRoom]:
        return self.room_repo.get_rooms_by_student(student_class_id)
    
    def send_message(self, room_id: int, sender_id: int, message: str) -> ChatMessage:
        msg = self.message_repo.create(
            chat_room_id=room_id,
            sender_id=sender_id,
            message=message
        )
        
        # Update room
        room = self.room_repo.get_by_id(room_id)
        if room:
            room.last_message = message[:500]
            room.last_message_at = datetime.utcnow()
            self.db.flush()
        
        return msg
    
    def get_messages(self, room_id: int, limit: int = 50, before: Optional[datetime] = None) -> List[ChatMessage]:
        messages = self.message_repo.get_by_room(room_id, limit, before)
        
        # Mark messages as read
        # Logic depends on user role - implemented in router
        return messages
    
    def get_unread_counts(self, room_id: int) -> Dict[str, int]:
        room = self.room_repo.get_by_id(room_id)
        if room:
            return {
                "student_unread": room.student_unread,
                "teacher_unread": room.teacher_unread
            }
        return {"student_unread": 0, "teacher_unread": 0}