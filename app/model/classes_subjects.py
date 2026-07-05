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
# classroom TABLE
# ============================================================

class ClassRoom(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "classroom"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # ===========================
    # Business ID
    # Example:
    # CLS10A
    # CLS12SCI
    # ===========================

    class_code = Column(
        String(30),
        nullable=False
    )

    # Example
    # Class 10

    class_name = Column(
        String(100),
        nullable=False
    )

    # Example
    # A
    # B
    # SCI
    # COM

    section = Column(
        String(30),
        nullable=False
    )

    # Example
    # Class 10-A

    display_name = Column(
        String(150),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    # ==========================================
    # Academic Session
    # ==========================================

    academic_sessions_id = Column(
        Integer,
        ForeignKey(
            "academic_sessions.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    # ==========================================
    # Class Teacher
    # ==========================================

    class_teacher_id = Column(
        String(30),
        ForeignKey(
            "teacher_profiles.teacher_id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # ==========================================
    # Capacity
    # ==========================================

    created_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    updated_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # ==========================================
    # Relationships
    # ==========================================

    academic_sessions = relationship(
        "AcademicSession",
        back_populates="classroom"
    )

    class_teacher = relationship(
        "TeacherProfile",
        foreign_keys=[class_teacher_id],
        back_populates="class_teacher_of"
    )

    class_subjects = relationship(
        "ClassSubject",
        back_populates="classroom",
        cascade="all, delete-orphan"
    )

    teacher_subjects = relationship(
        "TeacherSubject",
        back_populates="classroom",
        cascade="all, delete-orphan"
    )

    student_classes = relationship(
        "StudentClass",
        back_populates="classroom",
        cascade="all, delete-orphan"
    )

    timetable_entries = relationship(
        "ClassTimeTable",
        back_populates="classroom"
    )

    from_class_promotions = relationship("StudentPromotionHistory", foreign_keys="StudentPromotionHistory.from_classroom_id", back_populates="from_classroom")
    to_class_promotions = relationship("StudentPromotionHistory", foreign_keys="StudentPromotionHistory.to_classroom_id", back_populates="to_classroom")
    
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_classes")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_classes")




    __table_args__ = (

        UniqueConstraint(
            "academic_sessions_id",
            "class_code",
            name="uq_classroom_session_classcode"
        ),



        UniqueConstraint(
            "academic_sessions_id",
            "display_name",
            name="uq_classroom_session_display"
        ),
        UniqueConstraint(
            "academic_sessions_id",
            "class_name",
            "section"
        ),

    # -----------------------------------------
    # Indexes
    # -----------------------------------------

        Index(
                "idx_classroom_code",
                "class_code"
            ),

            Index(
                "idx_classroom_name",
                "class_name"
            ),

            Index(
                "idx_classroom_section",
                "section"
            ),

            Index(
                "idx_classroom_session",
                "academic_sessions_id"
            ),

            Index(
                "idx_classroom_teacher",
                "class_teacher_id"
            ),

            Index(
                "idx_classroom_active",
                "is_active"
            ),

        )


    @staticmethod
    def generate_class_code(
        class_name: str,
        section: str
    ) -> str:

        class_name = class_name.strip().upper()

        section = section.strip().upper()

        class_number = (
            class_name
            .replace("CLASS", "")
            .strip()
            .replace(" ", "")
        )

        return f"CLS{class_number}{section}"
    
    @staticmethod
    def generate_display_name(
        class_name: str,
        section: str
    ):

       return f"{class_name.strip()}-{section.strip().upper()}"


# ============================================================
# SUBJECT TABLE
# ============================================================

class Subject(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "subjects"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Business ID
    # MT10
    # SC10
    # EN10

    subject_code = Column(
        String(30),
        nullable=False,
        unique=True,
        index=True
    )

    subject_name = Column(
        String(100),
        nullable=False,
        index=True
    )

    description = Column(
        Text,
        nullable=True
    )

    display_order = Column(
        Integer,
        default=1,
        nullable=False
    )

    # Core / Elective

    subject_type = Column(
        String(20),
        default="Core",
        nullable=False
    )

    created_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    updated_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # ------------------------
    # Relationships
    # ------------------------

    class_subjects = relationship(
        "ClassSubject",
        back_populates="subject",
        cascade="all, delete-orphan"
    )

    teacher_subjects = relationship(
        "TeacherSubject",
        back_populates="subject",
        cascade="all, delete-orphan"
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_subjects"
    )

    updater = relationship(
        "User",
        foreign_keys=[updated_by],
        back_populates="updated_subjects"
    )

    

    __table_args__ = (

        UniqueConstraint(
            "subject_name",
            name="uq_subject_name"
        ),

        UniqueConstraint(
            "subject_code",
            name="uq_subject_code"
        ),

        Index(
            "idx_subject_name",
            "subject_name"
        ),

        Index(
            "idx_subject_active",
            "is_active"
        ),

    )

    @staticmethod
    def generate_subject_code(
        short_name: str,
        class_name: str
    ):

        cls = (
            class_name.upper()
            .replace("CLASS", "")
            .replace(" ", "")
        )

        return (
            short_name.upper()
            + cls
        )

    @property
    def display(self):

        return f"{self.subject_name} ({self.subject_code})"
    
    def activate(self):

        self.is_active = True

    def deactivate(self):

        self.is_active = False


# ============================================================
# CLASSSUBJECT TABLE
# ============================================================

class ClassSubject(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "class_subjects"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # ==========================================
    # Academic Session
    # ==========================================

    academic_sessions_id = Column(
        Integer,
        ForeignKey(
            "academic_sessions.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ==========================================
    # Class
    # ==========================================

    classroom_id = Column(
        Integer,
        ForeignKey(
            "classroom.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ==========================================
    # Subject
    # ==========================================

    subject_id = Column(
        Integer,
        ForeignKey(
            "subjects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    display_order = Column(
        Integer,
        default=1,
        nullable=False
    )

    created_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    updated_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # =================================================
    # Relationships
    # =================================================

    academic_sessions = relationship(
        "AcademicSession",
        back_populates="class_subjects"
    )

    classroom = relationship(
        "ClassRoom",
        back_populates="class_subjects"
    )

    subject = relationship(
        "Subject",
        back_populates="class_subjects"
    )

    teacher_subjects = relationship(
        "TeacherSubject",
        back_populates="class_subject",
        cascade="all, delete-orphan"
    )

    timetable_entries = relationship(
        "ClassTimeTable",
        back_populates="class_subject"
    )

    # =================================================
    # Constraints
    # =================================================

    __table_args__ = (

        UniqueConstraint(
            "academic_sessions_id",
            "classroom_id",
            "subject_id",
            name="uq_class_subject"
        ),

        Index(
            "idx_class_subject_class",
            "classroom_id"
        ),

        Index(
            "idx_class_subject_subject",
            "subject_id"
        ),

        Index(
            "idx_class_subject_session",
            "academic_sessions_id"
        ),

        Index(
            "idx_class_subject_active",
            "is_active"
        ),

    )


