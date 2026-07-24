from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.helpers.code_generators import (
    generate_duration_report_code,
    generate_zoom_file_code,
    generate_zoom_interaction_code,
    generate_interaction_report_code,
    generate_zoom_transcript_code,
)

# ============================================================
# NOTE
# ============================================================
#
# Ye saari tables maujuda "nsmanager_02.db" schema se match
# karke banayi gayi hain (columns / FKs / uniques bilkul same).
#
# In tables me DB me pehle se koi created_at / updated_at /
# is_active column exist nahi karta, isliye TimestampMixin /
# ActiveMixin yahan intentionally NOT lagaya gaya hai — taaki
# existing production data / schema se drift na ho. Agar aapko
# audit columns chahiye to bata dena, ek Alembic migration bana
# ke add kar denge.
#
# zoom_duration_report, zoom_interaction_report aur (topic.py
# me) student_topic_progress_report — "student_report" table ko
# reference karte hain jo is model package ka hissa nahi hai
# (assume kiya gaya hai ki "StudentReport" naam ka model kahin
# aur (report module) me already defined hai). Agar class ka
# naam alag hai to relationship() ke string reference ko us
# hisaab se update kar dena, warna mapper configure hote waqt
# error aayega.
#
# ============================================================


# ============================================================
# ZOOMMEETING TABLE
# ============================================================


class ZoomMeeting(Base):
    __tablename__ = "zoom_meeting"

    uuid = Column(String(64), primary_key=True)

    meeting_id = Column(BigInteger, index=True)

    account_id = Column(String(64))

    host_id = Column(String(64), index=True)

    topic = Column(String(300))

    type = Column(Integer)

    start_time = Column(DateTime, index=True)

    timezone = Column(String(64))

    duration = Column(Integer)

    total_size = Column(BigInteger)

    recording_count = Column(Integer)

    share_url = Column(String(500))

    recording_play_passcode = Column(String(255))

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------

    recording_files = relationship(
        "ZoomRecordingFile",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_zoom_meeting_meeting_id", "meeting_id"),
        Index("idx_zoom_meeting_host", "host_id"),
        Index("idx_zoom_meeting_start_time", "start_time"),
    )


# ============================================================
# ZOOMRECORDINGFILE TABLE
# ============================================================


class ZoomRecordingFile(Base):
    __tablename__ = "zoom_recording_file"

    id = Column(String(64), primary_key=True)

    meeting_uuid = Column(
        String(64),
        ForeignKey("zoom_meeting.uuid"),
        nullable=False,
        index=True,
    )

    recording_start = Column(DateTime)

    recording_end = Column(DateTime)

    file_type = Column(String(30))

    file_extension = Column(String(10))

    file_size = Column(BigInteger)

    play_url = Column(String(500))

    download_url = Column(String(500))

    status = Column(String(30), index=True)

    recording_type = Column(String(50))

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------

    meeting = relationship(
        "ZoomMeeting",
        back_populates="recording_files",
        lazy="joined",
    )

    transcripts = relationship(
        "ZoomTranscript",
        back_populates="recording_file",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    student_interactions = relationship(
        "ZoomStudentInteraction",
        back_populates="recording_file",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_zoom_recording_meeting", "meeting_uuid"),
        Index("idx_zoom_recording_status", "status"),
    )


# ============================================================
# ZOOMFILE TABLE
# ============================================================
# NOTE: current schema me is table ka koi FK relation kisi
# aur zoom table se nahi hai (standalone, matched file-index
# ke through referenced hota hai application logic me).
# ============================================================


class ZoomFile(Base):
    __tablename__ = "zoom_file"

    zoom_file_code = Column(String(30), primary_key=True, default=generate_zoom_file_code)

    file_initial = Column(String(255), unique=True, nullable=False, index=True)

    transcript_file = Column(String(500))

    audio_file = Column(String(500))

    audio_duration = Column(String(30))

    video_file = Column(String(500))

    video_duration = Column(String(30))

    raw_date = Column(String(30), nullable=False)

    raw_time = Column(String(30), nullable=False)

    date = Column(String(30), nullable=False, index=True)

    time = Column(String(30), nullable=False)

    __table_args__ = (
        UniqueConstraint("file_initial", name="uq_zoom_file_initial"),
        Index("idx_zoom_file_date", "date"),
    )


# ============================================================
# ZOOMTRANSCRIPT TABLE
# ============================================================


class ZoomTranscript(Base):
    __tablename__ = "zoom_transcript"

    zoom_transcript_code = Column(
        String(30),
        primary_key=True,
        default=generate_zoom_transcript_code,
    )

    zoom_file_id = Column(
        String(64),
        ForeignKey("zoom_recording_file.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # NOTE: "index" SQL me reserved-ish column hai, isliye
    # attribute alag rakha gaya hai aur actual DB column name
    # Column(...) ke pehle argument se explicitly map kiya hai.
    sequence_index = Column("index", Integer, nullable=False)

    start_time = Column(String(30), nullable=False)

    end_time = Column(String(30), nullable=False)

    duration = Column(Float, nullable=False)

    speaker = Column(String(150), nullable=False, index=True)

    text = Column(Text, nullable=False)

    class_name = Column(String(150))

    class_date = Column(DateTime, index=True)

    file_name = Column(String(255))

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------

    recording_file = relationship(
        "ZoomRecordingFile",
        back_populates="transcripts",
        lazy="joined",
    )

    __table_args__ = (
        Index("idx_zoom_transcript_file", "zoom_file_id"),
        Index("idx_zoom_transcript_class_date", "class_date"),
        Index("idx_zoom_transcript_speaker", "speaker"),
    )


# ============================================================
# ZOOMSTUDENTINTERACTION TABLE
# ============================================================


class ZoomStudentInteraction(Base):
    __tablename__ = "zoom_student_interaction"

    zoom_interaction_code = Column(
        String(30),
        primary_key=True,
        default=generate_zoom_interaction_code,
    )

    zoom_file_id = Column(
        String(64),
        ForeignKey("zoom_recording_file.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    class_date = Column(DateTime, index=True)

    class_name = Column(String(150))

    interaction_time = Column(String(30), nullable=False)

    interaction_duration = Column(Float, nullable=False)

    speaker_name = Column(String(150), nullable=False, index=True)

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------

    recording_file = relationship(
        "ZoomRecordingFile",
        back_populates="student_interactions",
        lazy="joined",
    )

    __table_args__ = (
        Index("idx_zoom_interaction_file", "zoom_file_id"),
        Index("idx_zoom_interaction_speaker", "speaker_name"),
        Index("idx_zoom_interaction_class_date", "class_date"),
    )


# ============================================================
# ZOOMDURATIONREPORT TABLE
# ============================================================


class ZoomDurationReport(Base):
    __tablename__ = "zoom_duration_report"

    duration_report_code = Column(
        String(30),
        primary_key=True,
        default=generate_duration_report_code,
    )

    report_id = Column(
        String(30),
        ForeignKey("student_report.report_code"),
        nullable=False,
        index=True,
    )

    mean_duration_minutes = Column(Integer)

    min_duration_minutes = Column(Integer)

    max_duration_minutes = Column(Integer)

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------
    # "StudentReport" is package se bahar defined maana gaya hai.

    report = relationship("StudentReport", lazy="joined")

    __table_args__ = (Index("idx_zoom_duration_report", "report_id"),)


# ============================================================
# ZOOMINTERACTIONREPORT TABLE
# ============================================================


class ZoomInteractionReport(Base):
    __tablename__ = "zoom_interaction_report"

    interaction_report_code = Column(
        String(30),
        primary_key=True,
        default=generate_interaction_report_code,
    )

    report_id = Column(
        String(30),
        ForeignKey("student_report.report_code"),
        nullable=False,
        index=True,
    )

    mean_interaction_count = Column(Integer)

    min_interaction_count = Column(Integer)

    max_interaction_count = Column(Integer)

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------
    # "StudentReport" is package se bahar defined maana gaya hai.

    report = relationship("StudentReport", lazy="joined")

    __table_args__ = (Index("idx_zoom_interaction_report", "report_id"),)
