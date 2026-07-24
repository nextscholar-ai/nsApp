# ============================================================
# model/attachment.py - Generic Attachment Table
# ============================================================
#
# A generic, polymorphic attachment store that lets any entity
# (assignments, study material, exams, chat messages, etc.)
# attach one or more files without needing a dedicated table.
#
# entity_type + entity_id identify the owning row, e.g.
#   entity_type="assignment", entity_id=42

from sqlalchemy import Column, Integer, LargeBinary, String

from app.api.database import Base
from app.core.mixins import ActiveMixin, AuditMixin, TimestampMixin
from app.helpers.code_generators import generate_uuid


class Attachment(
    Base,
    TimestampMixin,
    AuditMixin,
    ActiveMixin,
):
    __tablename__ = "attachments"

    attachment_code = Column(String(30), primary_key=True, default=generate_uuid)

    entity_type = Column(String(30), nullable=False, index=True)
    entity_id = Column(String(30), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)

    file_data = Column(LargeBinary, nullable=False)

    # NOTE: created_at / updated_at come from TimestampMixin and
    # created_by / updated_by come from AuditMixin - do not redeclare
    # them here, doing so previously caused duplicate-column errors
    # at table-definition time (SQLAlchemy raised on class creation).
