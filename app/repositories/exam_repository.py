# ============================================================
# repositories/exam_repository.py - Exam Repository
# ============================================================

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import ExamStatus
from app.model import Exam, ExamResult
from app.repositories.base_repository import BaseRepository


class ExamRepository(BaseRepository[Exam]):
    """Exam repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(Exam, db)

    def get_by_exam_id(self, exam_id: str) -> Exam | None:
        """Get exam by ID."""
        return self.db.query(Exam).filter(Exam.exam_id == exam_id).first()

    def get_by_teacher(self, teacher_id: str) -> list[Exam]:
        """Get exams by teacher."""
        return (
            self.db.query(Exam)
            .filter(Exam.teacher_subject_id == teacher_id)
            .order_by(Exam.exam_date.desc())
            .all()
        )

    def get_by_classroom(self, classroom_id: int) -> list[Exam]:
        """Get exams by classroom."""
        return (
            self.db.query(Exam)
            .filter(Exam.classroom_id == classroom_id)
            .order_by(Exam.exam_date.desc())
            .all()
        )

    def get_upcoming_exams(self, classroom_id: int, days: int = 30) -> list[Exam]:
        """Get upcoming exams for a classroom."""
        today = datetime.now(UTC).date()
        end_date = today + timedelta(days=days)

        return (
            self.db.query(Exam)
            .filter(
                Exam.classroom_id == classroom_id,
                Exam.exam_date >= today,
                Exam.exam_date <= end_date,
                Exam.status.in_([ExamStatus.PUBLISHED, ExamStatus.DRAFT]),
            )
            .order_by(Exam.exam_date)
            .all()
        )

    def get_active_exams(self) -> list[Exam]:
        """Get active exams."""
        today = datetime.now(UTC).date()
        return (
            self.db.query(Exam)
            .filter(Exam.exam_date == today, Exam.status == ExamStatus.PUBLISHED)
            .all()
        )

    def get_results_pending(self, teacher_id: str) -> list[Exam]:
        """Get exams with pending results."""
        return (
            self.db.query(Exam)
            .filter(
                Exam.teacher_subject_id == teacher_id,
                Exam.status == ExamStatus.COMPLETED,
                Exam.result_uploaded < Exam.total_students,
            )
            .all()
        )


class ExamResultRepository(BaseRepository[ExamResult]):
    """Exam result repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(ExamResult, db)

    def get_by_exam(self, exam_id: str) -> list[ExamResult]:
        """Get results by exam."""
        return (
            self.db.query(ExamResult)
            .filter(ExamResult.exam_id == exam_id)
            .order_by(ExamResult.rank_in_class)
            .all()
        )

    def get_by_student(self, student_class_id: str) -> list[ExamResult]:
        """Get results by student class."""
        return (
            self.db.query(ExamResult)
            .filter(ExamResult.student_class_id == student_class_id)
            .all()
        )

    def get_by_exam_student(
        self,
        exam_id: str,
        student_class_id: str,
    ) -> ExamResult | None:
        """Get result by exam and student."""
        return (
            self.db.query(ExamResult)
            .filter(
                ExamResult.exam_id == exam_id,
                ExamResult.student_class_id == student_class_id,
            )
            .first()
        )

    def get_or_create(self, exam_id: str, student_class_id: str) -> ExamResult:
        """Get or create exam result."""
        result = self.get_by_exam_student(exam_id, student_class_id)
        if not result:
            result = ExamResult(exam_id=exam_id, student_class_id=student_class_id)
            self.db.add(result)
            self.db.flush()
        return result

    def update_rankings(self, exam_id: str) -> None:
        """Update rankings for an exam."""
        results = self.get_by_exam(exam_id)

        # Sort by marks descending
        sorted_results = sorted(
            [r for r in results if not r.is_absent],
            key=lambda r: r.obtained_marks,
            reverse=True,
        )

        # Assign ranks
        for idx, result in enumerate(sorted_results, 1):
            result.rank_in_class = idx

        self.db.flush()

    def get_exam_stats(self, exam_id: str) -> dict[str, Any]:
        """Get statistics for an exam."""
        results = self.get_by_exam(exam_id)

        total = len(results)
        absent = sum(1 for r in results if r.is_absent)
        present = total - absent

        if present > 0:
            marks = [r.obtained_marks for r in results if not r.is_absent]
            avg_marks = sum(marks) / len(marks) if marks else 0
            max_marks = max(marks) if marks else 0
            min_marks = min(marks) if marks else 0
            pass_count = sum(
                1 for r in results if not r.is_absent and r.percentage >= 40
            )
        else:
            avg_marks = 0
            max_marks = 0
            min_marks = 0
            pass_count = 0

        return {
            "total_students": total,
            "present_students": present,
            "absent_students": absent,
            "average_marks": round(avg_marks, 2),
            "max_marks": round(max_marks, 2),
            "min_marks": round(min_marks, 2),
            "pass_count": pass_count,
            "pass_percentage": round((pass_count / present * 100), 2)
            if present > 0
            else 0,
        }
