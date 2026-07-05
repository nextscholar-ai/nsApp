import uuid
import secrets

from sqlalchemy import Enum

from datetime import datetime
from app.core.constants import *
from app.core.enums import *
from app.core.mixins import *
from app.helpers.code_generators import *
from app.helpers.validators import Validators
from app.helpers.date_utils import DateUtils
from app.helpers.security import SecurityUtils


from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    Time,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    Numeric

)

from sqlalchemy.orm import (
    relationship,
    declared_attr
)

from app.api.database import Base


# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# DAILYCLASS TABLE
# ============================================================

class DailyClass(Base, TimestampMixin, ActiveMixin):

    __tablename__ = "daily_classes"

    id = Column(
        Integer,
        primary_key=True
    )

    daily_class_id = Column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        nullable=False,
        index=True
    )

    classroom_id = Column(
        Integer,
        ForeignKey("classroom.id"),
        nullable=False,
        index=True
    )

    class_subject_id = Column(
        Integer,
        ForeignKey("class_subjects.id"),
        nullable=False,
        index=True
    )

    teacher_subject_id = Column(
        Integer,
        ForeignKey("teacher_subjects.id"),
        nullable=False,
        index=True
    )

    timetable_id = Column(
        Integer,
        ForeignKey("class_timetable.id"),
        nullable=True
    )

    class_date = Column(
        Date,
        nullable=False,
        index=True
    )

    topic = Column(
        String(300)
    )

    description = Column(
        Text
    )

    homework = Column(
        Text
    )

    lecture_status = Column(
        String(20),
        default="Scheduled",
        nullable=False,
        index=True
    )

    started_at = Column(DateTime)

    ended_at = Column(DateTime)

    total_minutes = Column(Integer)

    remarks = Column(Text)

    academic_sessions = relationship(
        "AcademicSession"
    )

    classroom = relationship(
        "ClassRoom"
    )

    class_subject = relationship(
        "ClassSubject"
    )

    teacher_subject = relationship(
        "TeacherSubject"
    )

    timetable = relationship(
        "ClassTimeTable"
    )

    students = relationship(
        "DailyClassStudent",
        back_populates="daily_class",
        cascade="all, delete-orphan"
    )


    __table_args__ = (

        UniqueConstraint(
            "teacher_subject_id",
            "class_date",
            "timetable_id",
            name="uq_daily_class"
        ),

        Index(
            "idx_daily_classes_class_date",
            "classroom_id",
            "class_date"
        ),

        Index(
            "idx_daily_classes_teacher",
            "teacher_subject_id",
            "class_date"
        ),

    )


# ============================================================
# DAILYCLASSSTUDENT TABLE
# ============================================================

class DailyClassStudent(Base, TimestampMixin):

    __tablename__ = "daily_class_students"

    id = Column(
        Integer,
        primary_key=True
    )

    daily_class_id = Column(
        Integer,
        ForeignKey("daily_classes.id"),
        nullable=False
    )

    student_class_id = Column(
        Integer,
        ForeignKey("student_classes.id"),
        nullable=False
    )

    attendance_status = Column(
        String(20),
        nullable=False,
        default="Present",
        index=True
    )

    is_late = Column(
        Boolean,
        default=False
    )

    late_minutes = Column(
        Integer,
        default=0
    )

    remarks = Column(
        Text
    )

    marked_by = Column(
        Integer,
        ForeignKey("users.id")
    )

    marked_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    daily_class = relationship(
        "DailyClass",
        back_populates="students"
    )

    student_class = relationship(
        "StudentClass"
    )

    marker = relationship(
        "User"
    )


    __table_args__ = (

        UniqueConstraint(
            "daily_class_id",
            "student_class_id",
            name="uq_daily_student"
        ),

        Index(
            "idx_daily_student",
            "student_class_id",
            "attendance_status"
        ),

    )


# ============================================================
# STUDENTATTENDANCE TABLE
# ============================================================

class StudentAttendance(Base, TimestampMixin):

    __tablename__ = "student_attendance"

    id = Column(
        Integer,
        primary_key=True
    )

    student_class_id = Column(
        Integer,
        ForeignKey("student_classes.id"),
        nullable=False,
        unique=True
    )

    total_classes = Column(
        Integer,
        default=0
    )

    present_classes = Column(
        Integer,
        default=0
    )

    absent_classes = Column(
        Integer,
        default=0
    )

    attendance_percentage = Column(
        Float,
        default=0
    )


    student_class = relationship(
        "StudentClass"
    )

    __table_args__ = (

        Index(
            "idx_student_attendance",
            "student_class_id"
        ),

    )


