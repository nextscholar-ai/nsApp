from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.enums import UserRole
from app.dependencies import require_role
from app.model import (
    User,
    ZoomDurationReport,
    ZoomFile,
    ZoomInteractionReport,
    ZoomMeeting,
    ZoomRecordingFile,
    ZoomStudentInteraction,
    ZoomTranscript,
)
from app.schemas.zoom import (
    ZoomDurationReportCreate,
    ZoomDurationReportResponse,
    ZoomDurationReportUpdate,
    ZoomFileCreate,
    ZoomFileResponse,
    ZoomFileUpdate,
    ZoomInteractionReportCreate,
    ZoomInteractionReportResponse,
    ZoomInteractionReportUpdate,
    ZoomMeetingCreate,
    ZoomMeetingResponse,
    ZoomMeetingUpdate,
    ZoomRecordingFileCreate,
    ZoomRecordingFileResponse,
    ZoomRecordingFileUpdate,
    ZoomStudentInteractionCreate,
    ZoomStudentInteractionResponse,
    ZoomStudentInteractionUpdate,
    ZoomTranscriptCreate,
    ZoomTranscriptResponse,
    ZoomTranscriptUpdate,
)

router = APIRouter(prefix="/zoom", tags=["Zoom"])

# ==================== ZOOM MEETINGS ====================


@router.get("/meetings", response_model=list[ZoomMeetingResponse])
async def list_zoom_meetings(
    host_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(ZoomMeeting)
    if host_id:
        query = query.filter(ZoomMeeting.host_id == host_id)
    return query.order_by(ZoomMeeting.start_time.desc()).all()


@router.get("/meetings/{uuid}", response_model=ZoomMeetingResponse)
async def get_zoom_meeting(
    uuid: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    meeting = db.query(ZoomMeeting).filter(ZoomMeeting.uuid == uuid).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Zoom meeting not found")
    return meeting


@router.post("/meetings", response_model=ZoomMeetingResponse, status_code=201)
async def create_zoom_meeting(
    data: ZoomMeetingCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    existing = db.query(ZoomMeeting).filter(ZoomMeeting.uuid == data.uuid).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Meeting with this UUID already exists",
        )
    meeting = ZoomMeeting(**data.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.put("/meetings/{uuid}", response_model=ZoomMeetingResponse)
async def update_zoom_meeting(
    uuid: str,
    data: ZoomMeetingUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    meeting = db.query(ZoomMeeting).filter(ZoomMeeting.uuid == uuid).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Zoom meeting not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(meeting, key, value)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.delete("/meetings/{uuid}")
async def delete_zoom_meeting(
    uuid: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    meeting = db.query(ZoomMeeting).filter(ZoomMeeting.uuid == uuid).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Zoom meeting not found")
    db.delete(meeting)
    db.commit()
    return {"success": True, "message": "Meeting deleted"}


# ==================== ZOOM RECORDING FILES ====================


@router.get("/recordings", response_model=list[ZoomRecordingFileResponse])
async def list_zoom_recordings(
    meeting_uuid: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(ZoomRecordingFile)
    if meeting_uuid:
        query = query.filter(ZoomRecordingFile.meeting_uuid == meeting_uuid)
    return query.order_by(ZoomRecordingFile.recording_start.desc()).all()


@router.get("/recordings/{id}", response_model=ZoomRecordingFileResponse)
async def get_zoom_recording(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    rec = db.query(ZoomRecordingFile).filter(ZoomRecordingFile.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recording not found")
    return rec


@router.post("/recordings", response_model=ZoomRecordingFileResponse, status_code=201)
async def create_zoom_recording(
    data: ZoomRecordingFileCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    existing = (
        db.query(ZoomRecordingFile).filter(ZoomRecordingFile.id == data.id).first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Recording with this ID already exists",
        )
    meeting = (
        db.query(ZoomMeeting).filter(ZoomMeeting.uuid == data.meeting_uuid).first()
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Referenced meeting not found")
    rec = ZoomRecordingFile(**data.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.put("/recordings/{id}", response_model=ZoomRecordingFileResponse)
async def update_zoom_recording(
    id: str,
    data: ZoomRecordingFileUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    rec = db.query(ZoomRecordingFile).filter(ZoomRecordingFile.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recording not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rec, key, value)
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/recordings/{id}")
async def delete_zoom_recording(
    id: str,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    rec = db.query(ZoomRecordingFile).filter(ZoomRecordingFile.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recording not found")
    db.delete(rec)
    db.commit()
    return {"success": True, "message": "Recording deleted"}


# ==================== ZOOM FILES ====================


@router.get("/files", response_model=list[ZoomFileResponse])
async def list_zoom_files(
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    return db.query(ZoomFile).order_by(ZoomFile.date.desc()).all()


@router.get("/files/{id}", response_model=ZoomFileResponse)
async def get_zoom_file(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    zf = db.query(ZoomFile).filter(ZoomFile.id == id).first()
    if not zf:
        raise HTTPException(status_code=404, detail="Zoom file not found")
    return zf


@router.post("/files", response_model=ZoomFileResponse, status_code=201)
async def create_zoom_file(
    data: ZoomFileCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    existing = (
        db.query(ZoomFile).filter(ZoomFile.file_initial == data.file_initial).first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="File with this initial already exists",
        )
    zf = ZoomFile(**data.model_dump())
    db.add(zf)
    db.commit()
    db.refresh(zf)
    return zf


@router.put("/files/{id}", response_model=ZoomFileResponse)
async def update_zoom_file(
    id: int,
    data: ZoomFileUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    zf = db.query(ZoomFile).filter(ZoomFile.id == id).first()
    if not zf:
        raise HTTPException(status_code=404, detail="Zoom file not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(zf, key, value)
    db.commit()
    db.refresh(zf)
    return zf


@router.delete("/files/{id}")
async def delete_zoom_file(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    zf = db.query(ZoomFile).filter(ZoomFile.id == id).first()
    if not zf:
        raise HTTPException(status_code=404, detail="Zoom file not found")
    db.delete(zf)
    db.commit()
    return {"success": True, "message": "Zoom file deleted"}


# ==================== ZOOM TRANSCRIPTS ====================


@router.get("/transcripts", response_model=list[ZoomTranscriptResponse])
async def list_zoom_transcripts(
    zoom_file_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(ZoomTranscript)
    if zoom_file_id:
        query = query.filter(ZoomTranscript.zoom_file_id == zoom_file_id)
    return query.order_by(ZoomTranscript.sequence_index).all()


@router.get("/transcripts/{id}", response_model=ZoomTranscriptResponse)
async def get_zoom_transcript(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    t = db.query(ZoomTranscript).filter(ZoomTranscript.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return t


@router.post("/transcripts", response_model=ZoomTranscriptResponse, status_code=201)
async def create_zoom_transcript(
    data: ZoomTranscriptCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    t = ZoomTranscript(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.put("/transcripts/{id}", response_model=ZoomTranscriptResponse)
async def update_zoom_transcript(
    id: int,
    data: ZoomTranscriptUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    t = db.query(ZoomTranscript).filter(ZoomTranscript.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(t, key, value)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/transcripts/{id}")
async def delete_zoom_transcript(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    t = db.query(ZoomTranscript).filter(ZoomTranscript.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")
    db.delete(t)
    db.commit()
    return {"success": True, "message": "Transcript deleted"}


# ==================== ZOOM STUDENT INTERACTIONS ====================


@router.get("/interactions", response_model=list[ZoomStudentInteractionResponse])
async def list_zoom_interactions(
    zoom_file_id: str | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(ZoomStudentInteraction)
    if zoom_file_id:
        query = query.filter(ZoomStudentInteraction.zoom_file_id == zoom_file_id)
    return query.order_by(ZoomStudentInteraction.class_date.desc()).all()


@router.get("/interactions/{id}", response_model=ZoomStudentInteractionResponse)
async def get_zoom_interaction(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    si = (
        db.query(ZoomStudentInteraction).filter(ZoomStudentInteraction.id == id).first()
    )
    if not si:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return si


@router.post(
    "/interactions",
    response_model=ZoomStudentInteractionResponse,
    status_code=201,
)
async def create_zoom_interaction(
    data: ZoomStudentInteractionCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    si = ZoomStudentInteraction(**data.model_dump())
    db.add(si)
    db.commit()
    db.refresh(si)
    return si


@router.put("/interactions/{id}", response_model=ZoomStudentInteractionResponse)
async def update_zoom_interaction(
    id: int,
    data: ZoomStudentInteractionUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    si = (
        db.query(ZoomStudentInteraction).filter(ZoomStudentInteraction.id == id).first()
    )
    if not si:
        raise HTTPException(status_code=404, detail="Interaction not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(si, key, value)
    db.commit()
    db.refresh(si)
    return si


@router.delete("/interactions/{id}")
async def delete_zoom_interaction(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    si = (
        db.query(ZoomStudentInteraction).filter(ZoomStudentInteraction.id == id).first()
    )
    if not si:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(si)
    db.commit()
    return {"success": True, "message": "Interaction deleted"}


# ==================== ZOOM DURATION REPORT ====================


@router.get("/duration-reports", response_model=list[ZoomDurationReportResponse])
async def list_duration_reports(
    report_id: int | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(ZoomDurationReport)
    if report_id:
        query = query.filter(ZoomDurationReport.report_id == report_id)
    return query.all()


@router.get("/duration-reports/{id}", response_model=ZoomDurationReportResponse)
async def get_duration_report(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    dr = db.query(ZoomDurationReport).filter(ZoomDurationReport.id == id).first()
    if not dr:
        raise HTTPException(status_code=404, detail="Duration report not found")
    return dr


@router.post(
    "/duration-reports",
    response_model=ZoomDurationReportResponse,
    status_code=201,
)
async def create_duration_report(
    data: ZoomDurationReportCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    dr = ZoomDurationReport(**data.model_dump())
    db.add(dr)
    db.commit()
    db.refresh(dr)
    return dr


@router.put("/duration-reports/{id}", response_model=ZoomDurationReportResponse)
async def update_duration_report(
    id: int,
    data: ZoomDurationReportUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    dr = db.query(ZoomDurationReport).filter(ZoomDurationReport.id == id).first()
    if not dr:
        raise HTTPException(status_code=404, detail="Duration report not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dr, key, value)
    db.commit()
    db.refresh(dr)
    return dr


@router.delete("/duration-reports/{id}")
async def delete_duration_report(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    dr = db.query(ZoomDurationReport).filter(ZoomDurationReport.id == id).first()
    if not dr:
        raise HTTPException(status_code=404, detail="Duration report not found")
    db.delete(dr)
    db.commit()
    return {"success": True, "message": "Duration report deleted"}


# ==================== ZOOM INTERACTION REPORT ====================


@router.get("/interaction-reports", response_model=list[ZoomInteractionReportResponse])
async def list_interaction_reports(
    report_id: int | None = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(ZoomInteractionReport)
    if report_id:
        query = query.filter(ZoomInteractionReport.report_id == report_id)
    return query.all()


@router.get("/interaction-reports/{id}", response_model=ZoomInteractionReportResponse)
async def get_interaction_report(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    ir = db.query(ZoomInteractionReport).filter(ZoomInteractionReport.id == id).first()
    if not ir:
        raise HTTPException(status_code=404, detail="Interaction report not found")
    return ir


@router.post(
    "/interaction-reports",
    response_model=ZoomInteractionReportResponse,
    status_code=201,
)
async def create_interaction_report(
    data: ZoomInteractionReportCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    ir = ZoomInteractionReport(**data.model_dump())
    db.add(ir)
    db.commit()
    db.refresh(ir)
    return ir


@router.put("/interaction-reports/{id}", response_model=ZoomInteractionReportResponse)
async def update_interaction_report(
    id: int,
    data: ZoomInteractionReportUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    ir = db.query(ZoomInteractionReport).filter(ZoomInteractionReport.id == id).first()
    if not ir:
        raise HTTPException(status_code=404, detail="Interaction report not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ir, key, value)
    db.commit()
    db.refresh(ir)
    return ir


@router.delete("/interaction-reports/{id}")
async def delete_interaction_report(
    id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    ir = db.query(ZoomInteractionReport).filter(ZoomInteractionReport.id == id).first()
    if not ir:
        raise HTTPException(status_code=404, detail="Interaction report not found")
    db.delete(ir)
    db.commit()
    return {"success": True, "message": "Interaction report deleted"}
