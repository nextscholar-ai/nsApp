from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import require_role
from app.model import StudentPromotionHistory, User
from app.schemas.promotion import (
    StudentPromotionHistoryCreate,
    StudentPromotionHistoryResponse,
    StudentPromotionHistoryUpdate,
)

router = APIRouter(prefix="/promotions", tags=["Student Promotions"])


@router.get("", response_model=list[StudentPromotionHistoryResponse])
async def list_promotions(
    student_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(StudentPromotionHistory)
    if student_id:
        query = query.filter(StudentPromotionHistory.student_id == student_id)
    return query.order_by(StudentPromotionHistory.promotion_date.desc()).all()


@router.get("/{id}", response_model=StudentPromotionHistoryResponse)
async def get_promotion(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    prom = (
        db.query(StudentPromotionHistory)
        .filter(StudentPromotionHistory.promotion_code == id)
        .first()
    )
    if not prom:
        raise HTTPException(status_code=404, detail="Promotion record not found")
    return prom


@router.post("", response_model=StudentPromotionHistoryResponse, status_code=201)
async def create_promotion(
    data: StudentPromotionHistoryCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    prom = StudentPromotionHistory(
        student_id=data.student_id,
        from_session_id=data.from_session_id,
        to_session_id=data.to_session_id,
        from_classroom_id=data.from_classroom_id,
        to_classroom_id=data.to_classroom_id,
        previous_roll_number=data.previous_roll_number,
        new_roll_number=data.new_roll_number,
        promotion_date=data.promotion_date or datetime.now(UTC).date(),
        promotion_type=data.promotion_type or "PROMOTED",
        remarks=data.remarks,
        promoted_by_user_id=current_user.id,
    )
    db.add(prom)
    db.commit()
    db.refresh(prom)
    return prom


@router.put("/{id}", response_model=StudentPromotionHistoryResponse)
async def update_promotion(
    id: str,
    data: StudentPromotionHistoryUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    prom = (
        db.query(StudentPromotionHistory)
        .filter(StudentPromotionHistory.promotion_code == id)
        .first()
    )
    if not prom:
        raise HTTPException(status_code=404, detail="Promotion record not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(prom, key, value)
    prom.promoted_by_user_id = current_user.id
    db.commit()
    db.refresh(prom)
    return prom


@router.delete("/{id}")
async def delete_promotion(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    prom = (
        db.query(StudentPromotionHistory)
        .filter(StudentPromotionHistory.promotion_code == id)
        .first()
    )
    if not prom:
        raise HTTPException(status_code=404, detail="Promotion record not found")
    db.delete(prom)
    db.commit()
    return {"success": True, "message": "Promotion record deleted"}
