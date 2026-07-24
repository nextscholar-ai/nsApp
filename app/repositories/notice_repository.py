# ============================================================
# repositories/notice_repository.py - Notice Repository
# ============================================================

from datetime import UTC, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.enums import NoticeAudience, NoticeType
from app.model import Notice
from app.repositories.base_repository import BaseRepository


class NoticeRepository(BaseRepository[Notice]):
    """Notice repository."""

    def __init__(self, db: Session) -> None:
        super().__init__(Notice, db)

    def get_by_notice_id(self, notice_id: str) -> Notice | None:
        """Get notice by ID."""
        return self.db.query(Notice).filter(Notice.notice_id == notice_id).first()

    def get_active_notices(self) -> list[Notice]:
        """Get active notices."""
        today = datetime.now(UTC).date()
        return (
            self.db.query(Notice)
            .filter(
                Notice.is_active,
                Notice.publish_date <= today,
                or_(Notice.expiry_date >= today, Notice.expiry_date is None),
            )
            .order_by(Notice.is_pinned.desc(), Notice.publish_date.desc())
            .all()
        )

    def get_by_type(self, notice_type: NoticeType) -> list[Notice]:
        """Get notices by type."""
        return (
            self.db.query(Notice)
            .filter(Notice.notice_type == notice_type, Notice.is_active)
            .all()
        )

    def get_by_audience(self, audience: NoticeAudience) -> list[Notice]:
        """Get notices by audience."""
        return (
            self.db.query(Notice)
            .filter(Notice.audience == audience, Notice.is_active)
            .all()
        )

    def get_pinned_notices(self) -> list[Notice]:
        """Get pinned notices."""
        return (
            self.db.query(Notice)
            .filter(Notice.is_pinned, Notice.is_active)
            .order_by(Notice.publish_date.desc())
            .all()
        )

    def get_user_notices(
        self,
        role: str,
        classroom_id: int | None = None,
    ) -> list[Notice]:
        """Get notices for a user based on role."""
        today = datetime.now(UTC).date()
        query = self.db.query(Notice).filter(
            Notice.is_active,
            Notice.publish_date <= today,
            or_(Notice.expiry_date >= today, Notice.expiry_date is None),
        )

        # Filter by audience
        if role == "student":
            query = query.filter(
                Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.STUDENT]),
            )
        elif role == "teacher":
            query = query.filter(
                Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.TEACHER]),
            )
        elif role == "admin":
            pass

        # For specific class notices
        if classroom_id:
            query = query.filter(
                or_(
                    Notice.classroom_id == classroom_id,
                    Notice.classroom_id is None,
                    Notice.audience == NoticeAudience.ALL,
                ),
            )

        return query.order_by(Notice.is_pinned.desc(), Notice.publish_date.desc()).all()

    def get_notices_by_class(self, classroom_id: int) -> list[Notice]:
        """Get notices for a specific class."""
        today = datetime.now(UTC).date()
        return (
            self.db.query(Notice)
            .filter(
                Notice.classroom_id == classroom_id,
                Notice.is_active,
                Notice.publish_date <= today,
                or_(Notice.expiry_date >= today, Notice.expiry_date is None),
            )
            .order_by(Notice.is_pinned.desc(), Notice.publish_date.desc())
            .all()
        )

    def get_expiring_notices(self, days: int = 3) -> list[Notice]:
        """Get notices expiring in the next days."""
        today = datetime.now(UTC).date()
        from datetime import timedelta

        end_date = today + timedelta(days=days)

        return (
            self.db.query(Notice)
            .filter(
                Notice.is_active,
                Notice.expiry_date >= today,
                Notice.expiry_date <= end_date,
            )
            .all()
        )
