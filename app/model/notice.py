from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.core.constants import MAX_CODE_LENGTH
from app.core.enums import NoticeAudience, NoticeType
from app.core.mixins import ActiveMixin, TimestampMixin
from app.helpers.code_generators import generate_notice_code

# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# NOTICE TABLE
# ============================================================


class Notice(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "notices"

    notice_code = Column(String(30), primary_key=True, default=generate_notice_code)

    # =====================================================
    # Academic
    # =====================================================

    academic_sessions_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("academic_sessions.session_code"),
        nullable=False,
        index=True,
    )

    classroom_id = Column(
        String(30),
        ForeignKey("classroom.class_code"),
        nullable=True,
        index=True,
    )

    # =====================================================
    # Notice Details
    # =====================================================

    title = Column(String(250), nullable=False)

    description = Column(Text, nullable=False)

    notice_type = Column(
        SAEnum(NoticeType),
        nullable=False,
        default=NoticeType.GENERAL,
        index=True,
    )

    audience = Column(
        SAEnum(NoticeAudience),
        nullable=False,
        default=NoticeAudience.ALL,
        index=True,
    )

    # =====================================================
    # Publish
    # =====================================================

    publish_date = Column(Date, nullable=False, index=True)

    expiry_date = Column(Date, nullable=True, index=True)

    # =====================================================
    # Attachment
    # =====================================================

    attachment_name = Column(String(255))

    attachment_path = Column(String(500))

    attachment_size = Column(Integer)

    mime_type = Column(String(100))

    # =====================================================
    # Pin Notice
    # =====================================================

    is_pinned = Column(Boolean, default=False, nullable=False, index=True)

    # =====================================================
    # Audit
    # =====================================================

    created_by = Column(String(30), ForeignKey("users.user_code"), nullable=False)

    updated_by = Column(String(30), ForeignKey("users.user_code"))

    deleted_by = Column(String(30), ForeignKey("users.user_code"))

    # =====================================================
    # Relationships
    # =====================================================

    academic_sessions = relationship("AcademicSession")

    classroom = relationship("ClassRoom", foreign_keys=[classroom_id])

    creator = relationship("User", foreign_keys=[created_by])

    updater = relationship("User", foreign_keys=[updated_by])

    deleter = relationship("User", foreign_keys=[deleted_by])

    # =====================================================
    # Constraints
    # =====================================================

    __table_args__ = (
        Index("idx_notice_publish", "publish_date", "audience"),
        Index("idx_notice_class", "classroom_id", "publish_date"),
        Index("idx_notice_pin", "is_pinned", "publish_date"),
        CheckConstraint(
            "(expiry_date IS NULL) OR (expiry_date >= publish_date)",
            name="ck_notice_expiry",
        ),
    )
