from datetime import datetime

from .common import BaseSchema


class ZoomMeetingBase(BaseSchema):
    uuid: str
    meeting_id: int | None = None
    account_id: str | None = None
    host_id: str | None = None
    topic: str | None = None
    type: int | None = None
    start_time: datetime | None = None
    timezone: str | None = None
    duration: int | None = None
    total_size: int | None = None
    recording_count: int | None = None
    share_url: str | None = None
    recording_play_passcode: str | None = None


class ZoomMeetingCreate(BaseSchema):
    uuid: str
    meeting_id: int | None = None
    account_id: str | None = None
    host_id: str | None = None
    topic: str | None = None
    type: int | None = None
    start_time: datetime | None = None
    timezone: str | None = None
    duration: int | None = None
    total_size: int | None = None
    recording_count: int | None = None
    share_url: str | None = None
    recording_play_passcode: str | None = None


class ZoomMeetingUpdate(BaseSchema):
    meeting_id: int | None = None
    account_id: str | None = None
    host_id: str | None = None
    topic: str | None = None
    type: int | None = None
    start_time: datetime | None = None
    timezone: str | None = None
    duration: int | None = None
    total_size: int | None = None
    recording_count: int | None = None
    share_url: str | None = None
    recording_play_passcode: str | None = None


class ZoomMeetingResponse(ZoomMeetingBase):
    pass


class ZoomRecordingFileBase(BaseSchema):
    id: str
    meeting_uuid: str | None = None
    recording_start: datetime | None = None
    recording_end: datetime | None = None
    file_type: str | None = None
    file_extension: str | None = None
    file_size: int | None = None
    play_url: str | None = None
    download_url: str | None = None
    status: str | None = None
    recording_type: str | None = None


class ZoomRecordingFileCreate(BaseSchema):
    id: str
    meeting_uuid: str
    recording_start: datetime | None = None
    recording_end: datetime | None = None
    file_type: str | None = None
    file_extension: str | None = None
    file_size: int | None = None
    play_url: str | None = None
    download_url: str | None = None
    status: str | None = None
    recording_type: str | None = None


class ZoomRecordingFileUpdate(BaseSchema):
    meeting_uuid: str | None = None
    recording_start: datetime | None = None
    recording_end: datetime | None = None
    file_type: str | None = None
    file_extension: str | None = None
    file_size: int | None = None
    play_url: str | None = None
    download_url: str | None = None
    status: str | None = None
    recording_type: str | None = None


class ZoomRecordingFileResponse(ZoomRecordingFileBase):
    pass


class ZoomFileBase(BaseSchema):
    file_initial: str
    transcript_file: str | None = None
    audio_file: str | None = None
    audio_duration: str | None = None
    video_file: str | None = None
    video_duration: str | None = None
    raw_date: str
    raw_time: str
    date: str
    time: str


class ZoomFileCreate(BaseSchema):
    file_initial: str
    transcript_file: str | None = None
    audio_file: str | None = None
    audio_duration: str | None = None
    video_file: str | None = None
    video_duration: str | None = None
    raw_date: str
    raw_time: str
    date: str
    time: str


class ZoomFileUpdate(BaseSchema):
    file_initial: str | None = None
    transcript_file: str | None = None
    audio_file: str | None = None
    audio_duration: str | None = None
    video_file: str | None = None
    video_duration: str | None = None
    raw_date: str | None = None
    raw_time: str | None = None
    date: str | None = None
    time: str | None = None


class ZoomFileResponse(ZoomFileBase):
    id: str


class ZoomTranscriptBase(BaseSchema):
    zoom_file_id: str
    sequence_index: int
    start_time: str
    end_time: str
    duration: float
    speaker: str
    text: str
    class_name: str | None = None
    class_date: datetime | None = None
    file_name: str | None = None


class ZoomTranscriptCreate(BaseSchema):
    zoom_file_id: str
    sequence_index: int
    start_time: str
    end_time: str
    duration: float
    speaker: str
    text: str
    class_name: str | None = None
    class_date: datetime | None = None
    file_name: str | None = None


class ZoomTranscriptUpdate(BaseSchema):
    zoom_file_id: str | None = None
    sequence_index: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration: float | None = None
    speaker: str | None = None
    text: str | None = None
    class_name: str | None = None
    class_date: datetime | None = None
    file_name: str | None = None


class ZoomTranscriptResponse(ZoomTranscriptBase):
    id: str


class ZoomStudentInteractionBase(BaseSchema):
    zoom_file_id: str
    class_date: datetime | None = None
    class_name: str | None = None
    interaction_time: str
    interaction_duration: float
    speaker_name: str


class ZoomStudentInteractionCreate(BaseSchema):
    zoom_file_id: str
    class_date: datetime | None = None
    class_name: str | None = None
    interaction_time: str
    interaction_duration: float
    speaker_name: str


class ZoomStudentInteractionUpdate(BaseSchema):
    zoom_file_id: str | None = None
    class_date: datetime | None = None
    class_name: str | None = None
    interaction_time: str | None = None
    interaction_duration: float | None = None
    speaker_name: str | None = None


class ZoomStudentInteractionResponse(ZoomStudentInteractionBase):
    id: str


class ZoomDurationReportBase(BaseSchema):
    report_id: str
    mean_duration_minutes: int | None = None
    min_duration_minutes: int | None = None
    max_duration_minutes: int | None = None


class ZoomDurationReportCreate(BaseSchema):
    report_id: str
    mean_duration_minutes: int | None = None
    min_duration_minutes: int | None = None
    max_duration_minutes: int | None = None


class ZoomDurationReportUpdate(BaseSchema):
    report_id: str | None = None
    mean_duration_minutes: int | None = None
    min_duration_minutes: int | None = None
    max_duration_minutes: int | None = None


class ZoomDurationReportResponse(ZoomDurationReportBase):
    id: str


class ZoomInteractionReportBase(BaseSchema):
    report_id: str
    mean_interaction_count: int | None = None
    min_interaction_count: int | None = None
    max_interaction_count: int | None = None


class ZoomInteractionReportCreate(BaseSchema):
    report_id: str
    mean_interaction_count: int | None = None
    min_interaction_count: int | None = None
    max_interaction_count: int | None = None


class ZoomInteractionReportUpdate(BaseSchema):
    report_id: str | None = None
    mean_interaction_count: int | None = None
    min_interaction_count: int | None = None
    max_interaction_count: int | None = None


class ZoomInteractionReportResponse(ZoomInteractionReportBase):
    id: str
