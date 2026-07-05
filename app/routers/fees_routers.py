# from fastapi import APIRouter
# from fastapi import Depends
# from fastapi import HTTPException

# from sqlalchemy.orm import Session

# from app.model import (
#     StudentProfile,
#     Fee,
#     teacherProfile,
#     adminProfile
# )

# from app.schemas import (
#     FeeCreate,
#     FeeUpdate,
#     FeeResponse
# )

# from app.dependencies import (
#     get_current_teacher,
#     get_db,
#     get_current_student
# )

# router = APIRouter(
#     prefix="/fees",
#     tags=["Fees"]
# )


# # =====================================================
# # CREATE FEE RECORD
# # Teacher/Admin Use
# # =====================================================

# @router.post(
#     "/{student_id}",
#     response_model=FeeResponse
# )
# def create_fee(

#     student_id: str,

#     data: FeeCreate,
#     teacher=Depends(
#         get_current_teacher
#     ),
#     db: Session = Depends(get_db)

# ):

#     student = (

#         db.query(StudentProfile)

#         .filter(
#             StudentProfile.student_id
#             == student_id
#         )

#         .first()
#     )

#     if not student:

#         raise HTTPException(
#             status_code=404,
#             detail="Student not found"
#         )

#     fee = Fee(

#         student_id=student.student_id,

#         month=data.month,

#         paid_amount=data.paid_fee,

#         payment_date=data.payment_date,

#         status=data.status
#     )

#     db.add(fee)

#     db.commit()

#     db.refresh(fee)

#     return {

#         "id": fee.id,

#         "student_name": student.student_name,

#         "phone_number": student.student_phone,

#         "month": fee.month,

#         "paid_fee": fee.paid_amount,

#         "payment_date": fee.payment_date,

#         "status": fee.status
#     }


# # =====================================================
# # UPDATE FEE RECORD
# # =====================================================

# @router.put(
#     "/{fee_id}",
#     response_model=FeeResponse
# )
# def update_fee(

#     fee_id: int,

#     data: FeeUpdate,
#     teacher=Depends(
#         get_current_teacher
#     ),  
#     db: Session = Depends(get_db)

# ):

#     fee = (

#         db.query(Fee)

#         .filter(
#             Fee.id == fee_id
#         )

#         .first()
#     )

#     if not fee:

#         raise HTTPException(
#             status_code=404,
#             detail="Fee record not found"
#         )

#     update_data = data.model_dump(
#         exclude_unset=True
#     )

#     for field, value in update_data.items():

#         setattr(
#             fee,
#             field,
#             value
#         )

#     db.commit()

#     db.refresh(fee)

#     student = (

#         db.query(StudentProfile)

#         .filter(
#             StudentProfile.student_id
#             == fee.student_id
#         )

#         .first()
#     )

#     return {

#         "id": fee.id,

#         "student_name": student.student_name,

#         "phone_number": student.student_phone,

#         "month": fee.month,

#         "paid_fee": fee.paid_amount,

#         "payment_date": fee.payment_date,

#         "status": fee.status
#     }


# # =====================================================
# # STUDENT VIEW FEES
# # =====================================================

# @router.get(
#     "/my-fees",
#     response_model=list[FeeResponse]
# )
# def my_fees(

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     records = (

#         db.query(Fee)

#         .filter(
#             Fee.student_id
#             == student.student_id
#         )

#         .order_by(
#             Fee.payment_date.desc()
#         )

#         .all()
#     )

#     result = []

#     for fee in records:

#         result.append({

#             "id": fee.id,

#             "student_name": student.student_name,

#             "phone_number": student.student_phone,

#             "month": fee.month,

#             "paid_fee": fee.paid_amount,

#             "payment_date": fee.payment_date,

#             "status": fee.status
#         })

#     return result


# # =====================================================
# # SINGLE FEE RECORD
# # =====================================================

# @router.get(
#     "/{fee_id}",
#     response_model=FeeResponse
# )
# def fee_detail(

#     fee_id: int,

#     student: StudentProfile = Depends(
#         get_current_student
#     ),

#     db: Session = Depends(get_db)

# ):

#     fee = (

#         db.query(Fee)

#         .filter(
#             Fee.id == fee_id,

#             Fee.student_id
#             == student.student_id
#         )

#         .first()
#     )

#     if not fee:

#         raise HTTPException(
#             status_code=404,
#             detail="Fee record not found"
#         )

#     return {

#         "id": fee.id,

#         "student_name": student.student_name,

#         "phone_number": student.student_phone,

#         "month": fee.month,

#         "paid_fee": fee.paid_amount,

#         "payment_date": fee.payment_date,

#         "status": fee.status
#     }


# ============================================================
# routers/fees_routers.py - Fee Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import date

from app.api.database import get_db
from app.model import User, Fee, StudentClass, StudentProfile
from app.schemas import (
    FeeResponse,
    FeeCreate,
    FeeUpdate,
    FeePaymentResponse,
    FeePaymentCreate,
    FeeSummaryResponse
)
from app.dependencies import (
    get_current_user,
    require_role
)
from app.core.enums import UserRole, FeeStatus

router = APIRouter(prefix="/fees", tags=["Fees"])

# ============================================================
# FEE CRUD
# ============================================================

@router.post("/", response_model=FeeResponse)
async def create_fee(
    fee_data: FeeCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new fee record.
    """
    # Check if student exists
    student_class = db.query(StudentClass).filter(
        StudentClass.id == fee_data.student_class_id
    ).first()
    
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student class record not found"
        )
    
    # Check if fee already exists for this month
    existing = db.query(Fee).filter(
        Fee.student_class_id == fee_data.student_class_id,
        Fee.fee_month == fee_data.fee_month,
        Fee.fee_year == fee_data.fee_year
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fee already exists for {fee_data.fee_month}/{fee_data.fee_year}"
        )
    
    new_fee = Fee(
        fee_id=fee_data.fee_id,
        academic_sessions_id=fee_data.academic_sessions_id,
        student_class_id=fee_data.student_class_id,
        fee_month=fee_data.fee_month,
        fee_year=fee_data.fee_year,
        total_amount=fee_data.total_amount,
        paid_amount=fee_data.paid_amount,
        discount_amount=fee_data.discount_amount,
        fine_amount=fee_data.fine_amount,
        due_date=fee_data.due_date,
        paid_date=fee_data.paid_date,
        status=fee_data.status,
        remarks=fee_data.remarks,
        created_by=current_user.id
    )
    
    db.add(new_fee)
    db.commit()
    db.refresh(new_fee)
    
    return FeeResponse.model_validate(new_fee)

@router.get("/", response_model=List[FeeResponse])
async def get_fees(
    student_class_id: Optional[int] = None,
    status: Optional[FeeStatus] = None,
    fee_month: Optional[int] = None,
    fee_year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get fees with filters.
    """
    query = db.query(Fee)
    
    if student_class_id:
        query = query.filter(Fee.student_class_id == student_class_id)
    elif current_user.role == UserRole.STUDENT:
        # For students, only show their fees
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        if student:
            student_class = db.query(StudentClass).filter(
                StudentClass.student_id == student.student_id
            ).first()
            if student_class:
                query = query.filter(Fee.student_class_id == student_class.id)
    
    if status:
        query = query.filter(Fee.status == status)
    
    if fee_month:
        query = query.filter(Fee.fee_month == fee_month)
    
    if fee_year:
        query = query.filter(Fee.fee_year == fee_year)
    
    fees = query.order_by(Fee.fee_year.desc(), Fee.fee_month.desc()).all()
    return [FeeResponse.model_validate(f) for f in fees]

@router.get("/{fee_id}", response_model=FeeResponse)
async def get_fee(
    fee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get fee by ID.
    """
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee record not found"
        )
    return FeeResponse.model_validate(fee)

@router.put("/{fee_id}", response_model=FeeResponse)
async def update_fee(
    fee_id: int,
    fee_data: FeeUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update fee record.
    """
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee record not found"
        )
    
    for key, value in fee_data.dict(exclude_unset=True).items():
        setattr(fee, key, value)
    
    fee.updated_by = current_user.id
    db.commit()
    db.refresh(fee)
    
    return FeeResponse.model_validate(fee)

# ============================================================
# FEE PAYMENT
# ============================================================

@router.post("/{fee_id}/pay", response_model=FeeResponse)
async def pay_fee(
    fee_id: int,
    payment_data: FeePaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pay a fee.
    """
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee record not found"
        )
    
    # For students, check if fee belongs to them
    if current_user.role == UserRole.STUDENT:
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        if student:
            student_class = db.query(StudentClass).filter(
                StudentClass.student_id == student.student_id
            ).first()
            if not student_class or fee.student_class_id != student_class.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only pay your own fees"
                )
    
    # Update fee
    fee.paid_amount += Decimal(str(payment_data.amount_paid))
    fee.paid_date = payment_data.payment_date
    
    # Update status
    if fee.paid_amount >= fee.total_amount + fee.fine_amount - fee.discount_amount:
        fee.status = FeeStatus.PAID
    elif fee.paid_amount > 0:
        fee.status = FeeStatus.PENDING
    
    fee.updated_by = current_user.id
    db.commit()
    db.refresh(fee)
    
    return FeeResponse.model_validate(fee)

# ============================================================
# FEE SUMMARY
# ============================================================

@router.get("/summary/student/{student_id}", response_model=FeeSummaryResponse)
async def get_student_fee_summary(
    student_id: str,
    academic_sessions_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get fee summary for a student.
    """
    student = db.query(StudentProfile).filter(
        StudentProfile.student_id == student_id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    student_class = db.query(StudentClass).filter(
        StudentClass.student_id == student_id,
        StudentClass.academic_sessions_id == academic_sessions_id
    ).first()
    
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this session"
        )
    
    fees = db.query(Fee).filter(
        Fee.student_class_id == student_class.id
    ).all()
    
    total = sum(f.total_amount for f in fees)
    paid = sum(f.paid_amount for f in fees)
    discount = sum(f.discount_amount for f in fees)
    fine = sum(f.fine_amount for f in fees)
    
    pending = total - paid
    
    return {
        "student_id": student_id,
        "student_name": student.student_name,
        "classroom": student_class.classroom.display_name if student_class.classroom else "",
        "total_fee": float(total),
        "paid_fee": float(paid),
        "pending_fee": float(pending),
        "discount_fee": float(discount),
        "fine_fee": float(fine),
        "status": "Paid" if pending == 0 else "Pending"
    }
