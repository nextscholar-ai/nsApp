# ============================================================
# repositories/attendance_repositories.py - Attendance Repositories
# ============================================================

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import AttendanceStatus
from app.model import (
    ClassTimeTable,
    DailyClass,
    DailyClassStudent,
    StudentAttendance,
    TeacherAvailability,
    TeacherSubject,
    TimeSlot,
    WeekDay,
)
from app.repositories.base_repository import BaseRepository


class WeekDayRepository(BaseRepository[WeekDay]):
    """Week day repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(WeekDay, db)

    def get_by_code(self, code: str) -> WeekDay | None:
        return self.db.query(WeekDay).filter(WeekDay.day_code == code).first()

    def get_ordered_days(self) -> list[WeekDay]:
        return (
            self.db.query(WeekDay)
            .filter(WeekDay.is_active)
            .order_by(WeekDay.display_order)
            .all()
        )


class TimeSlotRepository(BaseRepository[TimeSlot]):
    """Time slot repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(TimeSlot, db)

    def get_by_code(self, code: str) -> TimeSlot | None:
        return self.db.query(TimeSlot).filter(TimeSlot.slot_code == code).first()

    def get_ordered_slots(self) -> list[TimeSlot]:
        return (
            self.db.query(TimeSlot)
            .filter(TimeSlot.is_active)
            .order_by(TimeSlot.display_order)
            .all()
        )


class ClassTimeTableRepository(BaseRepository[ClassTimeTable]):
    """Class timetable repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(ClassTimeTable, db)

    def get_by_class_day_slot(
        self,
        classroom_id: str,
        week_day_id: str,
        time_slot_id: str,
        session_id: int,
    ) -> ClassTimeTable | None:
        return (
            self.db.query(ClassTimeTable)
            .filter(
                ClassTimeTable.classroom_id == classroom_id,
                ClassTimeTable.week_day_id == week_day_id,
                ClassTimeTable.time_slot_id == time_slot_id,
                ClassTimeTable.academic_sessions_id == session_id,
            )
            .first()
        )

    def get_timetable_by_class(
        self,
        classroom_id: str,
        session_id: int,
    ) -> list[ClassTimeTable]:
        # Eager-load relationships to ensure nested response serialization works.
        from sqlalchemy.orm import joinedload

        return (
            self.db.query(ClassTimeTable)
            .options(
                joinedload(ClassTimeTable.week_day),
                joinedload(ClassTimeTable.time_slot),
                # nested relationships use SQLAlchemy attributes (not string names)
                joinedload(ClassTimeTable.class_subject),
                joinedload(ClassTimeTable.teacher_subject),
                joinedload(ClassTimeTable.teacher_subject).joinedload(
                    TeacherSubject.subject,
                ),
                joinedload(ClassTimeTable.teacher_subject).joinedload(
                    TeacherSubject.teacher,
                ),
            )
            .filter(
                ClassTimeTable.classroom_id == classroom_id,
                ClassTimeTable.academic_sessions_id == session_id,
                ClassTimeTable.is_active,
            )
            .all()
        )


class TeacherAvailabilityRepository(BaseRepository[TeacherAvailability]):
    """Teacher availability repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(TeacherAvailability, db)

    def get_by_teacher_slot(
        self,
        teacher_subject_id: int,
        week_day_id: str,
        time_slot_id: str,
        session_id: int,
    ) -> TeacherAvailability | None:
        return (
            self.db.query(TeacherAvailability)
            .filter(
                TeacherAvailability.teacher_subject_id == teacher_subject_id,
                TeacherAvailability.week_day_id == week_day_id,
                TeacherAvailability.time_slot_id == time_slot_id,
                TeacherAvailability.academic_sessions_id == session_id,
            )
            .first()
        )

    def get_availability_by_teacher(
        self,
        teacher_subject_id: int,
        session_id: int,
    ) -> list[TeacherAvailability]:
        return (
            self.db.query(TeacherAvailability)
            .filter(
                TeacherAvailability.teacher_subject_id == teacher_subject_id,
                TeacherAvailability.academic_sessions_id == session_id,
                TeacherAvailability.is_active,
            )
            .all()
        )


class DailyClassRepository(BaseRepository[DailyClass]):
    """Daily class repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(DailyClass, db)

    def get_by_date(
        self,
        date_obj: date,
        teacher_subject_id: int,
    ) -> DailyClass | None:
        return (
            self.db.query(DailyClass)
            .filter(
                DailyClass.class_date == date_obj,
                DailyClass.teacher_subject_id == teacher_subject_id,
            )
            .first()
        )

    def get_classes_by_date(self, date_obj: date) -> list[DailyClass]:
        return self.db.query(DailyClass).filter(DailyClass.class_date == date_obj).all()

    def get_classes_by_teacher(
        self,
        teacher_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DailyClass]:
        return (
            self.db.query(DailyClass)
            .filter(
                DailyClass.teacher_subject_id == teacher_id,
                DailyClass.class_date >= start_date,
                DailyClass.class_date <= end_date,
            )
            .order_by(DailyClass.class_date.desc())
            .all()
        )

    def get_classes_by_classroom(
        self,
        classroom_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DailyClass]:
        return (
            self.db.query(DailyClass)
            .filter(
                DailyClass.classroom_id == classroom_id,
                DailyClass.class_date >= start_date,
                DailyClass.class_date <= end_date,
            )
            .order_by(DailyClass.class_date.desc())
            .all()
        )

    def get_upcoming_classes(self, teacher_id: str, days: int = 7) -> list[DailyClass]:
        today = datetime.now(UTC).date()
        end_date = today + timedelta(days=days)
        return (
            self.db.query(DailyClass)
            .filter(
                DailyClass.teacher_subject_id == teacher_id,
                DailyClass.class_date >= today,
                DailyClass.class_date <= end_date,
                DailyClass.lecture_status.in_(["Scheduled", "Ongoing"]),
            )
            .order_by(DailyClass.class_date)
            .all()
        )


class DailyClassStudentRepository(BaseRepository[DailyClassStudent]):
    """Daily class student repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(DailyClassStudent, db)

    def get_by_daily_class(self, daily_class_id: int) -> list[DailyClassStudent]:
        return (
            self.db.query(DailyClassStudent)
            .filter(DailyClassStudent.daily_class_id == daily_class_id)
            .all()
        )

    def get_by_student_class(self, student_class_id: str) -> list[DailyClassStudent]:
        return (
            self.db.query(DailyClassStudent)
            .filter(DailyClassStudent.student_class_id == student_class_id)
            .all()
        )

    def get_by_student_class_date_range(
        self,
        student_class_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DailyClassStudent]:
        return (
            self.db.query(DailyClassStudent)
            .join(DailyClass, DailyClass.id == DailyClassStudent.daily_class_id)
            .filter(
                DailyClassStudent.student_class_id == student_class_id,
                DailyClass.class_date >= start_date,
                DailyClass.class_date <= end_date,
            )
            .all()
        )

    def get_attendance_summary(self, student_class_id: str) -> dict[str, Any]:
        records = (
            self.db.query(DailyClassStudent)
            .filter(DailyClassStudent.student_class_id == student_class_id)
            .all()
        )

        total = len(records)
        present = sum(
            1 for r in records if r.attendance_status == AttendanceStatus.PRESENT
        )
        absent = sum(
            1 for r in records if r.attendance_status == AttendanceStatus.ABSENT
        )
        late = sum(1 for r in records if r.attendance_status == AttendanceStatus.LATE)
        excused = sum(
            1 for r in records if r.attendance_status == AttendanceStatus.EXCUSED
        )
        percentage = (present / total * 100) if total > 0 else 0

        return {
            "total_classes": total,
            "present": present,
            "absent": absent,
            "late": late,
            "excused": excused,
            "attendance_percentage": round(percentage, 2),
        }


class StudentAttendanceRepository(BaseRepository[StudentAttendance]):
    """Student attendance repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(StudentAttendance, db)

    def get_by_student_class(
        self,
        student_class_id: str,
    ) -> StudentAttendance | None:
        return (
            self.db.query(StudentAttendance)
            .filter(StudentAttendance.student_class_id == student_class_id)
            .first()
        )

    def get_or_create(self, student_class_id: str) -> StudentAttendance:
        attendance = self.get_by_student_class(student_class_id)
        if not attendance:
            attendance = StudentAttendance(student_class_id=student_class_id)
            self.db.add(attendance)
            self.db.flush()
        return attendance

    def update_from_records(self, student_class_id: str) -> StudentAttendance:
        attendance = self.get_or_create(student_class_id)

        records = (
            self.db.query(DailyClassStudent)
            .filter(DailyClassStudent.student_class_id == student_class_id)
            .all()
        )

        total = len(records)
        present = sum(
            1 for r in records if r.attendance_status == AttendanceStatus.PRESENT
        )
        absent = sum(
            1 for r in records if r.attendance_status == AttendanceStatus.ABSENT
        )

        attendance.total_classes = total
        attendance.present_classes = present
        attendance.absent_classes = absent
        attendance.attendance_percentage = (present / total * 100) if total > 0 else 0

        self.db.flush()
        return attendance
