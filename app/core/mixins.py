# app/core/mixins.py

from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean, Integer

class TimestampMixin:
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

class ActiveMixin:
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

class AuditMixin:
    created_by = Column(
        Integer,
        nullable=True
    )
    updated_by = Column(
        Integer,
        nullable=True
    )

class SoftDeleteMixin:
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    deleted_at = Column(
        DateTime,
        nullable=True
    )
    deleted_by = Column(
        Integer,
        nullable=True
    )