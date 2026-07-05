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
# WEEKDAY TABLE
# ============================================================

class WeekDay(
    TimestampMixin,
    ActiveMixin,
    Base
):
    __tablename__ = "week_days"

    # --------------------------------------------------
    # Primary Key
    # --------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # --------------------------------------------------
    # Business Code
    # --------------------------------------------------

    day_code = Column(
        String(3),
        nullable=False,
        unique=True
    )

    # Examples:
    # MON
    # TUE
    # WED

    # --------------------------------------------------

    day_name = Column(
        String(20),
        nullable=False,
        unique=True
    )

    # Monday
    # Tuesday

    # --------------------------------------------------

    display_order = Column(
        Integer,
        nullable=False,
        default=1
    )

    # Monday =1
    # Tuesday=2

    # --------------------------------------------------
    # Relationships
    # --------------------------------------------------

    timetable_entries = relationship(
        "ClassTimeTable",
        back_populates="week_day",
        cascade="all"
    )

    teacher_availability = relationship(
        "TeacherAvailability",
        back_populates="week_day",
        cascade="all"
    )

    # --------------------------------------------------
    # Indexes
    # --------------------------------------------------

    __table_args__ = (

        Index(
            "idx_weekday_code",
            "day_code"
        ),

        Index(
            "idx_weekday_name",
            "day_name"
        ),

        Index(
            "idx_weekday_order",
            "display_order"
        ),

        CheckConstraint(
            "display_order >= 1 AND display_order <= 7",
            name="ck_weekday_display_order"
        ),

    )

    # --------------------------------------------------

    def __repr__(self):

        return (
            f"<WeekDay("
            f"{self.day_code}"
            f")>"
        )


# ============================================================
# TIMESLOT TABLE
# ============================================================

class TimeSlot(
    TimestampMixin,
    ActiveMixin,
    Base
):
    __tablename__ = "time_slots"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    slot_code = Column(
        String(10),
        unique=True,
        nullable=False
    )

    # P1
    # P2
    # P3

    slot_name = Column(
        String(50),
        nullable=False
    )

    # First Period
    # Second Period

    start_time = Column(
        Time,
        nullable=False
    )

    end_time = Column(
        Time,
        nullable=False
    )

    duration_minutes = Column(
        Integer,
        nullable=False
    )

    display_order = Column(
        Integer,
        nullable=False
    )

    is_break = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # -----------------------------------------
    # Relationships
    # -----------------------------------------

    timetable_entries = relationship(
        "ClassTimeTable",
        back_populates="time_slot"
    )

    teacher_availability = relationship(
        "TeacherAvailability",
        back_populates="time_slot"
    )

    # -----------------------------------------

    __table_args__ = (

        Index(
            "idx_slot_code",
            "slot_code"
        ),

        Index(
            "idx_slot_order",
            "display_order"
        ),

        UniqueConstraint(
            "start_time",
            "end_time",
            name="uq_slot_time"
        ),

        CheckConstraint(
            "duration_minutes > 0",
            name="ck_slot_duration"
        ),

    )

    def __repr__(self):
        return (
            f"<TimeSlot("
            f"{self.slot_code}"
            f")>"
        )


# ============================================================
# CLASSTIMETABLE TABLE
# ============================================================

class ClassTimeTable(
    TimestampMixin,
    ActiveMixin,
    AuditMixin,
    Base
):
    __tablename__ = "class_timetable"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    timetable_id = Column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    # Example
    # TT-2026-00001

    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        nullable=False
    )

    classroom_id = Column(
        Integer,
        ForeignKey("classroom.id"),
        nullable=False
    )

    class_subject_id = Column(
        Integer,
        ForeignKey("class_subjects.id"),
        nullable=False
    )

    teacher_subject_id = Column(
        Integer,
        ForeignKey("teacher_subjects.id"),
        nullable=False
    )

    week_day_id = Column(
        Integer,
        ForeignKey("week_days.id"),
        nullable=False
    )

    time_slot_id = Column(
        Integer,
        ForeignKey("time_slots.id"),
        nullable=False
    )

    room_number = Column(
        String(50),
        nullable=True
    )

    remarks = Column(
        Text,
        nullable=True
    )

    # ---------------------------------------
    # Relationships
    # ---------------------------------------

    academic_sessions = relationship(
        "AcademicSession",
        back_populates="timetable_entries"
    )

    classroom = relationship(
        "ClassRoom",
        back_populates="timetable_entries"
    )

    class_subject = relationship(
        "ClassSubject",
        back_populates="timetable_entries"
    )

    teacher_subject = relationship(
        "TeacherSubject",
        back_populates="timetable_entries"
    )

    week_day = relationship(
        "WeekDay",
        back_populates="timetable_entries"
    )

    time_slot = relationship(
        "TimeSlot",
        back_populates="timetable_entries"
    )

    # ---------------------------------------
    # Constraints
    # ---------------------------------------

    __table_args__ = (

        # Same class cannot have two periods
        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "week_day_id",
            "time_slot_id",
            name="uq_class_slot"
        ),

        # Teacher cannot teach two classes simultaneously
        UniqueConstraint(
            "academic_sessions_id",
            "teacher_subject_id",
            "week_day_id",
            "time_slot_id",
            name="uq_teacher_slot"
        ),

        Index(
            "idx_timetable_session",
            "academic_sessions_id"
        ),

        Index(
            "idx_timetable_class",
            "classroom_id"
        ),

        Index(
            "idx_timetable_teacher",
            "teacher_subject_id"
        ),

        Index(
            "idx_timetable_day",
            "week_day_id"
        ),

        Index(
            "idx_timetable_slot",
            "time_slot_id"
        ),

    )

    def __repr__(self):
        return (
            f"<ClassTimeTable("
            f"{self.timetable_id}"
            f")>"
        )


# ============================================================
# TEACHERAVAILABILITY TABLE
# ============================================================

class TeacherAvailability(
    TimestampMixin,
    ActiveMixin,
    AuditMixin,
    Base
):
    __tablename__ = "teacher_availability"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    availability_id = Column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    # Example
    # TA-2026-000001

    academic_sessions_id = Column(
        Integer,
        ForeignKey("academic_sessions.id"),
        nullable=False
    )

    teacher_subject_id = Column(
        Integer,
        ForeignKey("teacher_subjects.id"),
        nullable=False
    )

    week_day_id = Column(
        Integer,
        ForeignKey("week_days.id"),
        nullable=False
    )

    time_slot_id = Column(
        Integer,
        ForeignKey("time_slots.id"),
        nullable=False
    )

    is_available = Column(
        Boolean,
        nullable=False,
        default=True
    )

    reason = Column(
        String(255),
        nullable=True
    )

    remarks = Column(
        Text,
        nullable=True
    )

    # ------------------------------------------------
    # Relationships
    # ------------------------------------------------

    academic_sessions = relationship(
        "AcademicSession",
        back_populates="teacher_availability"
    )

    teacher_subject = relationship(
        "TeacherSubject",
        back_populates="availability_slots"
    )

    week_day = relationship(
        "WeekDay",
        back_populates="teacher_availability"
    )

    time_slot = relationship(
        "TimeSlot",
        back_populates="teacher_availability"
    )

    # ------------------------------------------------
    # Constraints & Indexes
    # ------------------------------------------------

    __table_args__ = (

        UniqueConstraint(
            "academic_sessions_id",
            "teacher_subject_id",
            "week_day_id",
            "time_slot_id",
            name="uq_teacher_availability"
        ),

        Index(
            "idx_teacher_availability_teacher",
            "teacher_subject_id"
        ),

        Index(
            "idx_teacher_availability_day",
            "week_day_id"
        ),

        Index(
            "idx_teacher_availability_slot",
            "time_slot_id"
        ),

        Index(
            "idx_teacher_availability_session",
            "academic_sessions_id"
        ),
    )

    def __repr__(self):
        return (
            f"<TeacherAvailability("
            f"{self.availability_id}"
            f")>"
        )


