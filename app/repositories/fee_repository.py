# ============================================================
# repositories/fee_repository.py - Fee Repository
# ============================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from decimal import Decimal
from datetime import date

from app.model import Fee
from app.repositories.base_repository import BaseRepository
from app.core.enums import FeeStatus


class FeeRepository(BaseRepository[Fee]):
    """Fee repository."""
    
    def __init__(self, db: Session):
        super().__init__(Fee, db)
    
    def get_by_fee_id(self, fee_id: str) -> Optional[Fee]:
        """Get fee by ID."""
        return self.db.query(Fee).filter(Fee.fee_id == fee_id).first()
    
    def get_by_student_class(self, student_class_id: int) -> List[Fee]:
        """Get fees by student class."""
        return self.db.query(Fee).filter(
            Fee.student_class_id == student_class_id
        ).order_by(Fee.fee_year.desc(), Fee.fee_month.desc()).all()
    
    def get_by_student_month(self, student_class_id: int, month: int, year: int) -> Optional[Fee]:
        """Get fee by student, month, and year."""
        return self.db.query(Fee).filter(
            Fee.student_class_id == student_class_id,
            Fee.fee_month == month,
            Fee.fee_year == year
        ).first()
    
    def get_by_status(self, status: FeeStatus) -> List[Fee]:
        """Get fees by status."""
        return self.db.query(Fee).filter(Fee.status == status).all()
    
    def get_overdue_fees(self) -> List[Fee]:
        """Get overdue fees."""
        today = date.today()
        return self.db.query(Fee).filter(
            Fee.due_date < today,
            Fee.status == FeeStatus.PENDING
        ).all()
    
    def get_student_summary(self, student_class_id: int) -> Dict[str, Any]:
        """Get fee summary for a student."""
        fees = self.get_by_student_class(student_class_id)
        
        total = sum(f.total_amount for f in fees)
        paid = sum(f.paid_amount for f in fees)
        discount = sum(f.discount_amount for f in fees)
        fine = sum(f.fine_amount for f in fees)
        
        pending = total - paid
        
        return {
            "total_amount": float(total),
            "paid_amount": float(paid),
            "pending_amount": float(pending),
            "discount_amount": float(discount),
            "fine_amount": float(fine),
            "status": FeeStatus.PAID if pending == 0 else FeeStatus.PENDING
        }
    
    def get_session_summary(self, session_id: int) -> Dict[str, Any]:
        """Get fee summary for a session."""
        fees = self.db.query(Fee).filter(
            Fee.academic_sessions_id == session_id
        ).all()
        
        total = sum(f.total_amount for f in fees)
        paid = sum(f.paid_amount for f in fees)
        
        pending = total - paid
        
        return {
            "total_amount": float(total),
            "paid_amount": float(paid),
            "pending_amount": float(pending),
            "total_count": len(fees),
            "paid_count": sum(1 for f in fees if f.status == FeeStatus.PAID),
            "pending_count": sum(1 for f in fees if f.status == FeeStatus.PENDING)
        }
    
    def update_status(self, fee_id: int) -> Fee:
        """Update fee status based on paid amount."""
        fee = self.get_by_id(fee_id)
        if fee:
            total_due = fee.total_amount + fee.fine_amount - fee.discount_amount
            if fee.paid_amount >= total_due:
                fee.status = FeeStatus.PAID
            elif fee.paid_amount > 0:
                fee.status = FeeStatus.PENDING
            else:
                fee.status = FeeStatus.PENDING
            
            # Check if overdue
            if fee.status == FeeStatus.PENDING and fee.due_date < date.today():
                fee.status = FeeStatus.OVERDUE
            
            self.db.flush()
        return fee
