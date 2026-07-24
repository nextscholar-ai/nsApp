from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.core.constants import MAX_CODE_LENGTH
from app.core.mixins import ActiveMixin, TimestampMixin
from app.helpers.code_generators import generate_uuid

# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# DAILYCLASS TABLE
# ============================================================


class DailyClass(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "daily_classes"

    daily_class_code = Column(String(30), primary_key=True, default=generate_uuid)

    academic_sessions_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("academic_sessions.session_code"),
        nullable=False,
        index=True,
    )

    classroom_id = Column(
        String(30),
        ForeignKey("classroom.class_code"),
        nullable=False,
        index=True,
    )

    class_subject_id = Column(
        String(30),
        ForeignKey("class_subjects.class_subject_code"),
        nullable=False,
        index=True,
    )

    teacher_subject_id = Column(
        String(30),
        ForeignKey("teacher_subjects.teacher_subject_code"),
        nullable=False,
        index=True,
    )

    timetable_id = Column(
        String(30),
        ForeignKey("class_timetable.timetable_code"),
        nullable=True,
    )

    class_date = Column(Date, nullable=False, index=True)

    topic = Column(String(300))

    description = Column(Text)

    homework = Column(Text)

    lecture_status = Column(String(20), default="Scheduled", nullable=False, index=True)

    started_at = Column(DateTime)

    ended_at = Column(DateTime)

    total_minutes = Column(Integer)

    remarks = Column(Text)

    academic_sessions = relationship("AcademicSession")

    classroom = relationship("ClassRoom")

    class_subject = relationship("ClassSubject")

    teacher_subject = relationship("TeacherSubject")

    timetable = relationship("ClassTimeTable")

    students = relationship(
        "DailyClassStudent",
        back_populates="daily_class",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "teacher_subject_id",
            "class_date",
            "timetable_id",
            name="uq_daily_class",
        ),
        Index("idx_daily_classes_class_date", "classroom_id", "class_date"),
        Index("idx_daily_classes_teacher", "teacher_subject_id", "class_date"),
    )


# ============================================================
# DAILYCLASSSTUDENT TABLE
# ============================================================


class DailyClassStudent(Base, TimestampMixin):
    __tablename__ = "daily_class_students"

    daily_class_student_code = Column(String(30), primary_key=True, default=generate_uuid)

    daily_class_id = Column(
        String(30),
        ForeignKey("daily_classes.daily_class_code"),
        nullable=False,
    )

    student_class_id = Column(
        String(30),
        ForeignKey("student_classes.student_class_code"),
        nullable=False,
    )

    attendance_status = Column(
        String(20),
        nullable=False,
        default="Present",
        index=True,
    )

    is_late = Column(Boolean, default=False)

    late_minutes = Column(Integer, default=0)

    remarks = Column(Text)

    marked_by = Column(String(30), ForeignKey("users.user_code"))

    marked_at = Column(DateTime, default=datetime.utcnow)

    daily_class = relationship("DailyClass", back_populates="students")

    student_class = relationship("StudentClass")

    marker = relationship("User")

    __table_args__ = (
        UniqueConstraint("daily_class_id", "student_class_id", name="uq_daily_student"),
        Index("idx_daily_student", "student_class_id", "attendance_status"),
    )


# ============================================================
# STUDENTATTENDANCE TABLE
# ============================================================


class StudentAttendance(Base, TimestampMixin):
    __tablename__ = "student_attendance"

    attendance_code = Column(String(30), primary_key=True, default=generate_uuid)

    student_class_id = Column(
        String(30),
        ForeignKey("student_classes.student_class_code"),
        nullable=False,
        unique=True,
    )

    total_classes = Column(Integer, default=0)

    present_classes = Column(Integer, default=0)

    absent_classes = Column(Integer, default=0)

    attendance_percentage = Column(Float, default=0)

    student_class = relationship("StudentClass")

    __table_args__ = (Index("idx_student_attendance", "student_class_id"),)
