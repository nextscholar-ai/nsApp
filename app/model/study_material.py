import uuid
import secrets

from sqlalchemy import Enum as SAEnum

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
# STUDYMATERIAL TABLE
# ============================================================

class StudyMaterial(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "study_materials"

    id = Column(
        Integer,
        primary_key=True
    )

    material_id = Column(

        String(30),

        unique=True,

        nullable=False,

        default=generate_material_id,

        index=True

    )

    # ===========================================
    # Academic
    # ===========================================

    academic_sessions_id = Column(

        Integer,

        ForeignKey(
            "academic_sessions.id"
        ),

        nullable=False,

        index=True

    )

    classroom_id = Column(

        Integer,

        ForeignKey(
            "classroom.id"
        ),

        nullable=False,

        index=True

    )

    class_subject_id = Column(

        Integer,

        ForeignKey(
            "class_subjects.id"
        ),

        nullable=False,

        index=True

    )

    teacher_subject_id = Column(

        Integer,

        ForeignKey(
            "teacher_subjects.id"
        ),

        nullable=False,

        index=True

    )

    # ===========================================
    # Details
    # ===========================================

    title = Column(

        String(200),

        nullable=False

    )

    description = Column(

        Text

    )

    material_type = Column(

        SAEnum(MaterialType),

        nullable=False

    )

    # ===========================================
    # File
    # ===========================================

    file_name = Column(

        String(255),

        nullable=False

    )

    file_url = Column(

        String(500),

        nullable=False

    )

    file_size = Column(

        Integer

    )

    mime_type = Column(

        String(100)

    )

    download_count = Column(

        Integer,

        default=0

    )

    # ===========================================
    # Audit
    # ===========================================

    uploaded_by = Column(

        Integer,

        ForeignKey("users.id"),

        nullable=False

    )


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

    uploader = relationship(
        "User"
    )


    __table_args__ = (

        Index(

            "idx_material_class",

            "classroom_id",

            "class_subject_id"

        ),

        Index(

            "idx_material_teacher",

            "teacher_subject_id"

        ),

        UniqueConstraint(

            "class_subject_id",

            "title",

            name="uq_material_title"

        ),

    )


