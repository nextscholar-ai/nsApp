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
# NOTICE TABLE
# ============================================================

class Notice(

    Base,

    TimestampMixin,

    ActiveMixin

):

    __tablename__ = "notices"

    id = Column(
        Integer,
        primary_key=True
    )

    notice_id = Column(

        String(30),

        unique=True,

        nullable=False,

        default=generate_notice_code,

        index=True

    )

    # =====================================================
    # Academic
    # =====================================================

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

        nullable=True,

        index=True

    )

    # =====================================================
    # Notice Details
    # =====================================================

    title = Column(

        String(250),

        nullable=False

    )

    description = Column(

        Text,

        nullable=False

    )

    notice_type = Column(

        SAEnum(NoticeType),

        nullable=False,

        default=NoticeType.GENERAL,

        index=True

    )

    audience = Column(

        SAEnum(NoticeAudience),

        nullable=False,

        default=NoticeAudience.ALL,

        index=True

    )

    # =====================================================
    # Publish
    # =====================================================

    publish_date = Column(

        Date,

        nullable=False,

        index=True

    )

    expiry_date = Column(

        Date,

        nullable=True,

        index=True

    )

    # =====================================================
    # Attachment
    # =====================================================

    attachment_name = Column(

        String(255)

    )

    attachment_path = Column(

        String(500)

    )

    attachment_size = Column(

        Integer

    )

    mime_type = Column(

        String(100)

    )

    # =====================================================
    # Pin Notice
    # =====================================================

    is_pinned = Column(

        Boolean,

        default=False,

        nullable=False,

        index=True

    )

    # =====================================================
    # Audit
    # =====================================================

    created_by = Column(

        Integer,

        ForeignKey("users.id"),

        nullable=False

    )

    updated_by = Column(

        Integer,

        ForeignKey("users.id")

    )

    deleted_by = Column(

        Integer,

        ForeignKey("users.id")

    )

    # =====================================================
    # Relationships
    # =====================================================

    academic_sessions = relationship(
        "AcademicSession"
    )

    classroom = relationship(
        "ClassRoom",
        foreign_keys=[classroom_id]
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )

    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )

    deleter = relationship(
        "User",
        foreign_keys=[deleted_by]
    )

    # =====================================================
    # Constraints
    # =====================================================

    __table_args__ = (

        Index(

            "idx_notice_publish",

            "publish_date",

            "audience"

        ),

        Index(

            "idx_notice_class",

            "classroom_id",

            "publish_date"

        ),

        Index(

            "idx_notice_pin",

            "is_pinned",

            "publish_date"

        ),

        CheckConstraint(

            "(expiry_date IS NULL) OR (expiry_date >= publish_date)",

            name="ck_notice_expiry"

        ),

    )


