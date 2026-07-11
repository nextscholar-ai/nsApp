from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session


from app.model import (
    AcademicSession,
    StudentProfile,
    StudentClass,
    TeacherProfile,
    TeacherSubject,
    ClassTimeTable,
    WeekDay,
    TimeSlot,
    ClassRoom,
    ClassSubject,
)


class TimetableService:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------
    # Admin
    # -------------------------
    def admin_get_timetables(
        self,
        *,
        classroom_id: Optional[int] = None,
        teacher_subject_id: Optional[int] = None,
        class_subject_id: Optional[int] = None,
        week_day_id: Optional[int] = None,
    ) -> List[ClassTimeTable]:
        q = self.db.query(ClassTimeTable).filter(ClassTimeTable.is_active == True)

        if classroom_id is not None:
            q = q.filter(ClassTimeTable.classroom_id == classroom_id)
        if teacher_subject_id is not None:
            q = q.filter(ClassTimeTable.teacher_subject_id == teacher_subject_id)
        if class_subject_id is not None:
            q = q.filter(ClassTimeTable.class_subject_id == class_subject_id)
        if week_day_id is not None:
            q = q.filter(ClassTimeTable.week_day_id == week_day_id)

        # deterministic
        q = q.order_by(
            ClassTimeTable.academic_sessions_id.asc(),
            ClassTimeTable.classroom_id.asc(),
            ClassTimeTable.week_day_id.asc(),
            ClassTimeTable.time_slot_id.asc(),
        )
        return q.all()

    def admin_update_timetable(self, timetable_id: int, update_fields: dict) -> Optional[ClassTimeTable]:
        entry = (
            self.db.query(ClassTimeTable)
            .filter(ClassTimeTable.id == timetable_id)
            .first()
        )
        if not entry:
            return None

        # do not allow changing primary identity fields here (safety)
        # but allow other column updates that come in from schema.
        allowed = {
            "room_number",
            "remarks",
            "academic_sessions_id",
            "classroom_id",
            "class_subject_id",
            "teacher_subject_id",
            "week_day_id",
            "time_slot_id",
            "is_active",
        }

        for k, v in update_fields.items():
            if k in allowed:
                setattr(entry, k, v)

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def admin_delete_timetable(self, timetable_id: int) -> bool:
        entry = (
            self.db.query(ClassTimeTable)
            .filter(ClassTimeTable.id == timetable_id)
            .first()
        )
        if not entry:
            return False

        # soft delete if model has is_active
        if hasattr(entry, "is_active"):
            entry.is_active = False
        self.db.commit()
        return True

    # -------------------------
    # Student
    # -------------------------
    def _get_current_academic_session_id(self) -> int:
        session = self.db.query(AcademicSession).filter(AcademicSession.is_current == True).first()
        if not session:
            raise HTTPException(status_code=404, detail="Current academic session not found")
        return session.id

    def student_get_timetable(self, *, student_user_id: int) -> List[dict]:
        current_session_id = self._get_current_academic_session_id()

        student = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.user_id == student_user_id)
            .first()
        )
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")

        student_classes = (
            self.db.query(StudentClass)
            .filter(
                StudentClass.student_id == student.student_id,
                StudentClass.academic_sessions_id == current_session_id,
                StudentClass.status == "ACTIVE",
            )
            .all()
        )

        if not student_classes:
            return []

        classroom_ids = [sc.classroom_id for sc in student_classes]

        # Join timetable -> weekday/timeslot -> class_subject -> teacher_subject -> teacher_profile
        q = (
            self.db.query(
                WeekDay.day_name.label("day"),
                TimeSlot.start_time.label("start_time"),
                TimeSlot.end_time.label("end_time"),
                ClassSubject.subject_name.label("subject"),
                TeacherProfile.teacher_name.label("teacher"),
                ClassTimeTable.id.label("timetable_id"),
            )
            .select_from(ClassTimeTable)
            .join(WeekDay, WeekDay.id == ClassTimeTable.week_day_id)
            .join(TimeSlot, TimeSlot.id == ClassTimeTable.time_slot_id)
            .join(ClassSubject, ClassSubject.id == ClassTimeTable.class_subject_id)
            .join(TeacherSubject, TeacherSubject.id == ClassTimeTable.teacher_subject_id)
            .join(TeacherProfile, TeacherProfile.teacher_id == TeacherSubject.teacher_id)
            .filter(
                ClassTimeTable.is_active == True,
                ClassTimeTable.academic_sessions_id == current_session_id,
                ClassTimeTable.classroom_id.in_(classroom_ids),
            )
            .order_by(
                WeekDay.display_order.asc(),
                TimeSlot.display_order.asc(),
                ClassTimeTable.classroom_id.asc(),
            )
        )

        rows = q.all()
        return [
            {
                "day": r.day,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "subject": r.subject,
                "teacher": r.teacher,
            }
            for r in rows
        ]

    # -------------------------
    # Teacher
    # -------------------------
    def teacher_get_timetable(self, *, teacher_user_id: int) -> List[dict]:
        current_session_id = self._get_current_academic_session_id()

        teacher = (
            self.db.query(TeacherProfile)
            .filter(TeacherProfile.user_id == teacher_user_id)
            .first()
        )
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher profile not found")

        allowed_teacher_subject_ids = (
            self.db.query(TeacherSubject.id)
            .filter(
                TeacherSubject.teacher_id == teacher.teacher_id,
                TeacherSubject.academic_sessions_id == current_session_id,
                TeacherSubject.is_active == True,
            )
            .all()
        )
        allowed_teacher_subject_ids = [x[0] for x in allowed_teacher_subject_ids]

        if not allowed_teacher_subject_ids:
            return []

        q = (
            self.db.query(
                ClassRoom.display_name.label("class"),
                ClassSubject.subject_name.label("subject"),
                WeekDay.day_name.label("day"),
                TimeSlot.start_time.label("start_time"),
                TimeSlot.end_time.label("end_time"),
            )
            .select_from(ClassTimeTable)
            .join(ClassRoom, ClassRoom.id == ClassTimeTable.classroom_id)
            .join(ClassSubject, ClassSubject.id == ClassTimeTable.class_subject_id)
            .join(WeekDay, WeekDay.id == ClassTimeTable.week_day_id)
            .join(TimeSlot, TimeSlot.id == ClassTimeTable.time_slot_id)
            .filter(
                ClassTimeTable.is_active == True,
                ClassTimeTable.academic_sessions_id == current_session_id,
                ClassTimeTable.teacher_subject_id.in_(allowed_teacher_subject_ids),
            )
            .order_by(
                ClassRoom.class_name.asc(),
                WeekDay.display_order.asc(),
                TimeSlot.display_order.asc(),
            )
        )

        rows = q.all()
        return [
            {
                "class": r.class_,

                "subject": r.subject,
                "day": r.day,
                "time": f"{r.start_time} - {r.end_time}",
            }
            for r in rows
        ]

