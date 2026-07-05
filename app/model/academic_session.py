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
# ACADEMICSESSION TABLE
# ============================================================

class AcademicSession(

    Base,

    TimestampMixin,

    ActiveMixin,

    AuditMixin

):

    __tablename__ = "academic_sessions"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    session_code = Column(
        String(MAX_CODE_LENGTH),
        unique=True,
        nullable=False,
        index=True
    )

    session_name = Column(
        String(20),
        unique=True,
        nullable=False
    )

    start_year = Column(
        Integer,
        nullable=False
    )

    end_year = Column(
        Integer,
        nullable=False
    )

    start_date = Column(
        Date,
        nullable=False
    )

    end_date = Column(
        Date,
        nullable=False
    )

    is_current = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    description = Column(
        Text,
        nullable=True
    )

    __table_args__ = (

        CheckConstraint(
            "end_year > start_year",
            name="ck_session_year"
        ),

        Index(
            "idx_session_name",
            "session_name"
        ),

        Index(
            "idx_session_active",
            "is_current"
        ),


        UniqueConstraint(
            "session_name",
            name="uq_session_name"
        ),

    )


    classroom = relationship(
        "ClassRoom",
        back_populates="academic_sessions",
        cascade="all, delete-orphan"
    )

    class_subjects = relationship(
        "ClassSubject",
        back_populates="academic_sessions",
        cascade="all, delete-orphan"
    )

    teacher_subjects = relationship(
        "TeacherSubject",
        back_populates="academic_sessions",
        cascade="all, delete-orphan"
    )

    student_classes = relationship(
        "StudentClass",
        back_populates="academic_sessions",
        cascade="all, delete-orphan"
    )

    timetable_entries = relationship(
        "ClassTimeTable",
        back_populates="academic_sessions"
    )

    teacher_availability = relationship(
        "TeacherAvailability",
        back_populates="academic_sessions"
    )

   
    from_session_promotions = relationship("StudentPromotionHistory", foreign_keys="StudentPromotionHistory.from_session_id", back_populates="from_session")
    to_session_promotions = relationship("StudentPromotionHistory", foreign_keys="StudentPromotionHistory.to_session_id", back_populates="to_session")

