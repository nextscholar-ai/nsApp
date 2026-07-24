# ============================================================
# services/academic_service.py - Academic & Attendance Service
# ============================================================

import logging
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import AttendanceStatus
from app.model import (
    ClassTimeTable,
    DailyClass,
    DailyClassStudent,
    TeacherAvailability,
    TimeSlot,
    WeekDay,
)
from app.repositories.attendance_repository import (
    ClassTimeTableRepository,
    DailyClassRepository,
    DailyClassStudentRepository,
    StudentAttendanceRepository,
    TeacherAvailabilityRepository,
    TimeSlotRepository,
    WeekDayRepository,
)
from app.repositories.core_repositories import StudentClassRepository

logger = logging.getLogger(__name__)


class AcademicService:
    """Academic and attendance service."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.weekday_repo = WeekDayRepository(db)
        self.timeslot_repo = TimeSlotRepository(db)
        self.timetable_repo = ClassTimeTableRepository(db)
        self.availability_repo = TeacherAvailabilityRepository(db)
        self.daily_class_repo = DailyClassRepository(db)
        self.daily_student_repo = DailyClassStudentRepository(db)
        self.attendance_repo = StudentAttendanceRepository(db)
        self.student_class_repo = StudentClassRepository(db)

    # ==================== WEEK DAY ====================

    def get_all_weekdays(self) -> list[WeekDay]:
        return self.weekday_repo.get_ordered_days()

    def create_weekday(self, **kwargs) -> WeekDay:
        return self.weekday_repo.create(**kwargs)

    # ==================== TIME SLOT ====================

    def get_all_timeslots(self) -> list[TimeSlot]:
        return self.timeslot_repo.get_ordered_slots()

    def create_timeslot(self, **kwargs) -> TimeSlot:
        return self.timeslot_repo.create(**kwargs)

    # ==================== TIMETABLE ====================

    def create_timetable(self, **kwargs) -> ClassTimeTable:
        return self.timetable_repo.create(**kwargs)

    def get_class_timetable(
        self,
        classroom_id: int,
        session_id: int,
    ) -> list[ClassTimeTable]:
        return self.timetable_repo.get_timetable_by_class(classroom_id, session_id)

    def delete_timetable(self, timetable_id: int) -> bool:
        return self.timetable_repo.delete_by_id(timetable_id)

    # ==================== TEACHER AVAILABILITY ====================

    def create_availability(self, **kwargs) -> TeacherAvailability:
        return self.availability_repo.create(**kwargs)

    def get_teacher_availability(
        self,
        teacher_subject_id: int,
        session_id: int,
    ) -> list[TeacherAvailability]:
        return self.availability_repo.get_availability_by_teacher(
            teacher_subject_id,
            session_id,
        )

    def update_availability(
        self,
        availability_id: int,
        **kwargs,
    ) -> TeacherAvailability | None:
        return self.availability_repo.update_by_id(availability_id, **kwargs)

    # ==================== DAILY CLASS ====================

    def create_daily_class(self, **kwargs) -> DailyClass:
        return self.daily_class_repo.create(**kwargs)

    def get_daily_class(self, daily_class_id: int) -> DailyClass | None:
        return self.daily_class_repo.get_by_id(daily_class_id)

    def get_daily_classes_by_date(self, date_obj: date) -> list[DailyClass]:
        return self.daily_class_repo.get_classes_by_date(date_obj)

    def get_daily_classes_by_teacher(
        self,
        teacher_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DailyClass]:
        return self.daily_class_repo.get_classes_by_teacher(
            teacher_id,
            start_date,
            end_date,
        )

    def update_daily_class(self, daily_class_id: int, **kwargs) -> DailyClass | None:
        return self.daily_class_repo.update_by_id(daily_class_id, **kwargs)

    def delete_daily_class(self, daily_class_id: int) -> bool:
        return self.daily_class_repo.delete_by_id(daily_class_id)

    # ==================== ATTENDANCE ====================

    def mark_attendance(
        self,
        daily_class_id: int,
        attendance_list: list[dict[str, Any]],
    ) -> list[DailyClassStudent]:
        marked = []
        for item in attendance_list:
            student_class_id = item.get("student_class_id")
            existing = (
                self.daily_student_repo.db.query(DailyClassStudent)
                .filter(
                    DailyClassStudent.daily_class_id == daily_class_id,
                    DailyClassStudent.student_class_id == student_class_id,
                )
                .first()
            )

            if existing:
                existing.attendance_status = item.get(
                    "attendance_status",
                    AttendanceStatus.PRESENT,
                )
                existing.is_late = item.get("is_late", False)
                existing.late_minutes = item.get("late_minutes", 0)
                existing.remarks = item.get("remarks")
                existing.marked_at = datetime.now(UTC)
                marked.append(existing)
            else:
                new_record = DailyClassStudent(
                    daily_class_id=daily_class_id,
                    student_class_id=student_class_id,
                    attendance_status=item.get(
                        "attendance_status",
                        AttendanceStatus.PRESENT,
                    ),
                    is_late=item.get("is_late", False),
                    late_minutes=item.get("late_minutes", 0),
                    remarks=item.get("remarks"),
                    marked_at=datetime.now(UTC),
                )
                self.db.add(new_record)
                marked.append(new_record)

        self.db.flush()

        # Update attendance summary for all students
        for item in attendance_list:
            self.attendance_repo.update_from_records(item["student_class_id"])

        return marked

    def get_attendance_by_daily_class(
        self,
        daily_class_id: int,
    ) -> list[DailyClassStudent]:
        return self.daily_student_repo.get_by_daily_class(daily_class_id)

    def get_student_attendance_summary(self, student_class_id: str) -> dict[str, Any]:
        return self.daily_student_repo.get_attendance_summary(student_class_id)

    def get_student_attendance_by_date_range(
        self,
        student_class_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DailyClassStudent]:
        return self.daily_student_repo.get_by_student_class_date_range(
            student_class_id,
            start_date,
            end_date,
        )

    def get_class_attendance_summary(
        self,
        classroom_id: int,
        session_id: int,
    ) -> dict[str, Any]:
        students = self.student_class_repo.get_students_by_class(
            classroom_id,
            session_id,
        )
        summary = []
        for student in students:
            attendance = self.get_student_attendance_summary(student.id)
            summary.append(
                {
                    "student_id": student.student_id,
                    "roll_number": student.roll_number,
                    "attendance": attendance,
                },
            )
        return {
            "classroom_id": classroom_id,
            "total_students": len(students),
            "students": summary,
        }
