# from app.dependencies import get_current_teacher
# from fastapi import (
#     APIRouter,
#     Depends,
#     UploadFile,
#     File,
#     Form,
#     HTTPException
# )

# from app.schemas import NoticeResponse

# from sqlalchemy.orm import Session

# from app.api.database import get_db

# from app.model import (
#     Notice,
#     NoticeAttachment
# )

# import os
# import shutil
# import uuid

# router = APIRouter(
#     prefix="/notices",
#     tags=["Notice Board"]
# )

# UPLOAD_DIR = "uploads/notices"

# os.makedirs(
#     UPLOAD_DIR,
#     exist_ok=True
# )


# @router.post("/", response_model=NoticeResponse)
# def create_notice(
#     title: str = Form(...),
#     description: str = Form(None),
#     files: list[UploadFile] = File([]),
#     teacher=Depends(
#         get_current_teacher
#     ),
#     db: Session = Depends(get_db)
# ):

#     notice = Notice(
#         title=title,
#         description=description
#     )

#     db.add(notice)
#     db.commit()
#     db.refresh(notice)

#     for file in files:

#         extension = os.path.splitext(
#             file.filename
#         )[1]

#         unique_name = (
#             str(uuid.uuid4()) +
#             extension
#         )

#         file_path = os.path.join(
#             UPLOAD_DIR,
#             unique_name
#         )

#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(
#                 file.file,
#                 buffer
#             )

#         file_url = f"/uploads/notices/{unique_name}"

#         attachment = NoticeAttachment(
#             notice_id=notice.id,
#             file_name=file.filename,
#             file_path=file_url,
#             file_type=file.content_type
#         )

#         db.add(attachment)

#     db.commit()

    

#     db.refresh(notice)

#     notice = db.query(Notice).filter(
#         Notice.id == notice.id
#     ).first()

#     return notice


# @router.get("/",response_model=list[NoticeResponse])
# def get_all_notices(
#     db: Session = Depends(get_db)
# ):

#     notices = db.query(
#         Notice
#     ).order_by(
#         Notice.created_at.desc()
#     ).all()

#     return notices



# @router.get("/{notice_id}",response_model=NoticeResponse)
# def get_notice(
#     notice_id: int,
#     db: Session = Depends(get_db)
# ):

#     notice = db.query(
#         Notice
#     ).filter(
#         Notice.id == notice_id
#     ).first()

#     if not notice:
#         raise HTTPException(
#             status_code=404,
#             detail="Notice not found"
#         )

#     return notice



# @router.delete("/{notice_id}")
# def delete_notice(
#     notice_id: int,
#     teacher=Depends(
#         get_current_teacher
#     ),  
#     db: Session = Depends(get_db)
# ):

#     notice = db.query(
#         Notice
#     ).filter(
#         Notice.id == notice_id
#     ).first()

#     if not notice:
#         raise HTTPException(
#             status_code=404,
#             detail="Notice not found"
#         )

#     for attachment in notice.attachments:

#         if os.path.exists(
#             attachment.file_path
#         ):
#             os.remove(
#                 attachment.file_path
#             )

#     db.delete(notice)

#     db.commit()

#     return {
#         "message": "Notice deleted"
#     }



# ============================================================
# routers/notice_routers.py - Notice Routes
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api.database import get_db
from app.model import User, Notice, ClassRoom
from app.schemas import (
    NoticeResponse,
    NoticeCreate,
    NoticeUpdate,
    NoticeFilterRequest,
    PaginatedResponseSchema
)
from app.dependencies import (
    get_current_user,
    require_role
)
from app.core.enums import UserRole, NoticeType, NoticeAudience

router = APIRouter(prefix="/notices", tags=["Notice Board"])

# ============================================================
# NOTICE CRUD
# ============================================================

@router.post("/", response_model=NoticeResponse)
async def create_notice(
    notice_data: NoticeCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new notice.
    """
    new_notice = Notice(
        notice_id=notice_data.notice_id,
        academic_sessions_id=notice_data.academic_sessions_id,
        classroom_id=notice_data.classroom_id,
        title=notice_data.title,
        description=notice_data.description,
        notice_type=notice_data.notice_type,
        audience=notice_data.audience,
        publish_date=notice_data.publish_date,
        expiry_date=notice_data.expiry_date,
        attachment_name=notice_data.attachment_name,
        attachment_path=notice_data.attachment_path,
        attachment_size=notice_data.attachment_size,
        mime_type=notice_data.mime_type,
        is_pinned=notice_data.is_pinned,
        created_by=current_user.id
    )
    
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    
    return NoticeResponse.model_validate(new_notice)

@router.get("/", response_model=List[NoticeResponse])
async def get_notices(
    notice_type: Optional[NoticeType] = None,
    audience: Optional[NoticeAudience] = None,
    is_pinned: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notices with filters.
    """
    query = db.query(Notice).filter(
        Notice.is_active == True,
        Notice.publish_date <= date.today()
    )
    
    if notice_type:
        query = query.filter(Notice.notice_type == notice_type)
    
    if is_pinned is not None:
        query = query.filter(Notice.is_pinned == is_pinned)
    
    # Filter by audience
    if current_user.role == UserRole.STUDENT:
        query = query.filter(
            Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.STUDENT])
        )
    elif current_user.role == UserRole.TEACHER:
        query = query.filter(
            Notice.audience.in_([NoticeAudience.ALL, NoticeAudience.TEACHER])
        )
    elif current_user.role == UserRole.ADMIN:
        pass
    
    # Order by pinned first, then by publish date
    notices = query.order_by(
        Notice.is_pinned.desc(),
        Notice.publish_date.desc()
    ).all()
    
    return [NoticeResponse.model_validate(n) for n in notices]

@router.get("/{notice_id}", response_model=NoticeResponse)
async def get_notice(
    notice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notice by ID.
    """
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found"
        )
    return NoticeResponse.model_validate(notice)

@router.put("/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: int,
    notice_data: NoticeUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update notice.
    """
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found"
        )
    
    for key, value in notice_data.dict(exclude_unset=True).items():
        setattr(notice, key, value)
    
    notice.updated_by = current_user.id
    db.commit()
    db.refresh(notice)
    
    return NoticeResponse.model_validate(notice)

@router.delete("/{notice_id}")
async def delete_notice(
    notice_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete notice.
    """
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found"
        )
    
    notice.is_active = False
    notice.deleted_by = current_user.id
    db.commit()
    
    return {"success": True, "message": "Notice deleted successfully"}

# ============================================================
# NOTICE PIN/UNPIN
# ============================================================

@router.post("/{notice_id}/pin")
async def pin_notice(
    notice_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Pin a notice.
    """
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found"
        )
    
    notice.is_pinned = True
    db.commit()
    
    return {"success": True, "message": "Notice pinned successfully"}

@router.post("/{notice_id}/unpin")
async def unpin_notice(
    notice_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Unpin a notice.
    """
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found"
        )
    
    notice.is_pinned = False
    db.commit()
    
    return {"success": True, "message": "Notice unpinned successfully"}
