# ============================================================
# repositories/notice_repository.py - Notice Repository
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date

from app.model import Notice
from app.repositories.base_repository import BaseRepository
from app.core.enums import NoticeType, NoticeAudience


class NoticeRepository(BaseRepository[Notice]):
    """Notice repository."""
    
    def __init__(self, db: Session):
        super().__init__(Notice, db)
    
    def get_by_notice_id(self, notice_id: str) -> Optional[Notice]:
        """Get notice by ID."""
        return self.db.query(Notice).filter(Notice.notice_id == notice_id).first()
    
    def get_active_notices(self) -> List[Notice]:
        """Get active notices."""
        today = date.today()
        return self.db.query(Notice).filter(
            Notice.is_active == True,
            Notice.publish_date <= today,
            or_(
                Notice.expiry_date >= today,
                Notice.expiry_date == None
            )
        ).order_by(Notice.is_pinned.desc(), Notice.publish_date.desc()).all()
    
    def get_by_type(self, notice_type: NoticeType) -> List[Notice]:
        """Get notices by type."""
        return self.db.query(Notice).filter(
            Notice.notice_type == notice_type,
            Notice.is_active == True
        ).all()
    
    def get_by_audience(self, audience: NoticeAudience) -> List[Notice]:
        """Get notices by audience."""
        return self.db.query(Notice).filter(
            Notice.audience == audience,
            Notice.is_active == True
        ).all()
    
    def get_pinned_notices(self) -> List[Notice]:
        """Get pinned notices."""
        return self.db.query(Notice).filter(
            Notice.is_pinned == True,
            Notice.is_active == True
        ).order_by(Notice.publish_date.desc()).all()
    
    def get_user_notices(self, role: str, classroom_id: Optional[int] = None) -> List[Notice]:
        """Get notices for a user based on role."""
        today = date.today()
        query = self.db.query(Notice).filter(
            Notice.is_active == True,
            Notice.publish_date <= today,
            or_(
                Notice.expiry_date >= today,
                Notice.expiry_date == None
            )
        )
        
        # Filter by audience
        if role == "student":
            query = query.filter(
                Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.STUDENT])
            )
        elif role == "teacher":
            query = query.filter(
                Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.TEACHER])
            )
        elif role == "admin":
            pass
        
        # For specific class notices
        if classroom_id:
            query = query.filter(
                or_(
                    Notice.classroom_id == classroom_id,
                    Notice.classroom_id == None,
                    Notice.audience == NoticeAudience.ALL
                )
            )
        
        return query.order_by(
            Notice.is_pinned.desc(),
            Notice.publish_date.desc()
        ).all()
    
    def get_notices_by_class(self, classroom_id: int) -> List[Notice]:
        """Get notices for a specific class."""
        today = date.today()
        return self.db.query(Notice).filter(
            Notice.classroom_id == classroom_id,
            Notice.is_active == True,
            Notice.publish_date <= today,
            or_(
                Notice.expiry_date >= today,
                Notice.expiry_date == None
            )
        ).order_by(Notice.is_pinned.desc(), Notice.publish_date.desc()).all()
    
    def get_expiring_notices(self, days: int = 3) -> List[Notice]:
        """Get notices expiring in the next days."""
        today = date.today()
        from datetime import timedelta
        end_date = today + timedelta(days=days)
        
        return self.db.query(Notice).filter(
            Notice.is_active == True,
            Notice.expiry_date >= today,
            Notice.expiry_date <= end_date
        ).all()
