from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.core.constants import MAX_CODE_LENGTH
from app.core.enums import MaterialType
from app.core.mixins import ActiveMixin, TimestampMixin
from app.helpers.code_generators import generate_material_code

# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# STUDYMATERIAL TABLE
# ============================================================


class StudyMaterial(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "study_materials"

    material_code = Column(String(30), primary_key=True, default=generate_material_code)

    # ===========================================
    # Academic
    # ===========================================

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

    # ===========================================
    # Details
    # ===========================================

    title = Column(String(200), nullable=False)

    description = Column(Text)

    material_type = Column(SAEnum(MaterialType), nullable=False)

    # ===========================================
    # File
    # ===========================================

    file_name = Column(String(255), nullable=False)

    file_url = Column(String(500), nullable=False)

    file_size = Column(Integer)

    mime_type = Column(String(100))

    download_count = Column(Integer, default=0)

    # ===========================================
    # Audit
    # ===========================================

    uploaded_by = Column(String(30), ForeignKey("users.user_code"), nullable=False)

    academic_sessions = relationship("AcademicSession")

    classroom = relationship("ClassRoom")

    class_subject = relationship("ClassSubject")

    teacher_subject = relationship("TeacherSubject")

    uploader = relationship("User")

    __table_args__ = (
        Index("idx_material_class", "classroom_id", "class_subject_id"),
        Index("idx_material_teacher", "teacher_subject_id"),
        UniqueConstraint("class_subject_id", "title", name="uq_material_title"),
    )
