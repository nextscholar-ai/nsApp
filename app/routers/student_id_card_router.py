import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.dependencies import get_current_user, require_role
from app.core.enums import UserRole

from app.services.student_id_card_service import StudentIDCardService


router = APIRouter(prefix="/student", tags=["Student ID Card"])


@router.post("/id-card/{student_id}")
async def generate_id_card(
    student_id: str,
    regenerate: bool = False,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """ADMIN generates or regenerates student's ID card.

    `student_id` ab id, email, ya naam - teeno accept karta hai."""
    from app.services.identifier_resolver_service import IdentifierResolverService
    student_id = IdentifierResolverService(db).resolve_student_id(student_id)

    service = StudentIDCardService(db)
    card = service.generate_or_regenerate_card(student_id=student_id, admin_user=current_user, regenerate=regenerate)
    return {
        "success": True,
        "card_id": card.id,
        "student_id": card.student_id,
        "academic_sessions_id": card.academic_sessions_id,
        "pdf_path": card.pdf_path,
        "qr_code_path": card.qr_code_path,
    }


@router.get("/id-card/{student_id}")
async def view_id_card(
    student_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """VIEW allowed for Admin/Teacher/Student (student can view own only).

    `student_id` ab id, email, ya naam - teeno accept karta hai."""
    from app.services.identifier_resolver_service import IdentifierResolverService
    student_id = IdentifierResolverService(db).resolve_student_id(student_id)

    service = StudentIDCardService(db)
    card = service.get_card_for_view(student_id=student_id, current_user=current_user)
    return {
        "id": card.id,
        "student_id": card.student_id,
        "academic_sessions_id": card.academic_sessions_id,
        "institute_logo_path": card.institute_logo_path,
        "institute_name": card.institute_name,
        "institute_contact_number": card.institute_contact_number,
        "academic_session_label": card.academic_session_label,
        "date_of_joining": card.date_of_joining,
        "valid_till": card.valid_till,
        "student_photo_path": card.student_photo_path,
        "student_name": card.student_name,
        "parent_name": card.parent_name,
        "class_display_name": card.class_display_name,
        "student_id_business": card.student_id_business,
        "qr_code_path": card.qr_code_path,
        "pdf_path": card.pdf_path,
    }


@router.get("/id-card/{student_id}/download")
async def download_id_card(
    student_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download generated PDF (front side only).

    `student_id` ab id, email, ya naam - teeno accept karta hai."""
    from app.services.identifier_resolver_service import IdentifierResolverService
    student_id = IdentifierResolverService(db).resolve_student_id(student_id)

    service = StudentIDCardService(db)
    card = service.get_card_for_view(student_id=student_id, current_user=current_user)

    if not card.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not generated yet")

    # card.pdf_path is stored as relative path under repo or absolute depending on generator.
    path = card.pdf_path
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    filename = f"student_id_card_{student_id}.pdf"
    return FileResponse(path, media_type="application/pdf", filename=filename)


@router.get("/id-card/all")
async def list_all_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """ADMIN: list all cards."""
    service = StudentIDCardService(db)
    items, total = service.list_all_cards(page=page, page_size=page_size)

    def to_resp(c):
        return {
            "id": c.id,
            "student_id": c.student_id,
            "academic_sessions_id": c.academic_sessions_id,
            "institute_logo_path": c.institute_logo_path,
            "institute_name": c.institute_name,
            "institute_contact_number": c.institute_contact_number,
            "academic_session_label": c.academic_session_label,
            "date_of_joining": c.date_of_joining,
            "valid_till": c.valid_till,
            "student_photo_path": c.student_photo_path,
            "student_name": c.student_name,
            "parent_name": c.parent_name,
            "class_display_name": c.class_display_name,
            "student_id_business": c.student_id_business,
            "qr_code_path": c.qr_code_path,
            "pdf_path": c.pdf_path,
        }

    return {
        "success": True,
        "data": [to_resp(x) for x in items],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }

