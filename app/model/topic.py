from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.api.database import Base
from app.helpers.code_generators import (
    generate_topic_code,
    generate_topic_progress_code,
    generate_uuid,
)

# ============================================================
# NOTE
# ============================================================
#
# Ye tables maujuda "nsmanager_02.db" schema se match karke
# banayi gayi hain:
#
#   Topic                      -> table "ka_topic"
#   TopicProgress               -> table "ka_topic_progress"
#   StudentTopicProgressReport  -> table "student_topic_progress_report"
#
# DB me pehle se koi created_at / updated_at / is_active column
# nahi hai, isliye TimestampMixin / ActiveMixin yahan lagaya
# nahi gaya — schema drift na ho isliye.
#
# "ka_course", "ka_student" aur "student_report" tables is
# model package ka hissa nahi hain (Khan-Academy sync module /
# report module me already maujud maane gaye hain). Unke liye
# relationship() me "KaCourse", "KaStudent", "StudentReport"
# class names assume kiye gaye hain — agar actual class names
# alag hain to yahan update kar dena.
#
# ============================================================


# ============================================================
# TOPIC TABLE  (ka_topic)
# ============================================================


class Topic(Base):
    __tablename__ = "ka_topic"

    topic_code = Column(String(30), primary_key=True, default=generate_topic_code)

    course_id = Column(String(30), ForeignKey("ka_course.ka_course_code"), index=True)

    topic_id = Column(String(200), unique=True, index=True)

    topic_name = Column(String(200), index=True)

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------
    # "KaCourse" is package se bahar defined maana gaya hai.

    course = relationship("KaCourse", lazy="joined")

    progress_entries = relationship(
        "TopicProgress",
        back_populates="topic",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    report_links = relationship(
        "StudentTopicProgressReport",
        back_populates="topic",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("topic_id", name="uq_ka_topic_topic_id"),
        Index("idx_ka_topic_course", "course_id"),
        Index("idx_ka_topic_name", "topic_name"),
    )


# ============================================================
# TOPICPROGRESS TABLE  (ka_topic_progress)
# ============================================================


class TopicProgress(Base):
    __tablename__ = "ka_topic_progress"

    topic_progress_code = Column(
        String(30),
        primary_key=True,
        default=generate_topic_progress_code,
    )

    student_id = Column(String(30), ForeignKey("ka_student.ka_student_code"), index=True)

    course_id = Column(String(30), ForeignKey("ka_course.ka_course_code"), index=True)

    topic_id = Column(String(30), ForeignKey("ka_topic.topic_code"), index=True)

    point_available = Column(Integer)

    point_earned = Column(Integer)

    percentage_earned = Column(Integer)

    date = Column(Date, index=True)

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------
    # "KaStudent" aur "KaCourse" is package se bahar defined
    # maana gaya hai.

    student = relationship("KaStudent", lazy="joined")

    course = relationship("KaCourse", lazy="joined")

    topic = relationship("Topic", back_populates="progress_entries", lazy="joined")

    report_links = relationship(
        "StudentTopicProgressReport",
        back_populates="topic_progress",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("student_id", "topic_id", "date", name="_topic_progress_uc"),
        Index("idx_topic_progress_student", "student_id"),
        Index("idx_topic_progress_topic", "topic_id"),
        Index("idx_topic_progress_date", "date"),
    )


# ============================================================
# STUDENTTOPICPROGRESSREPORT TABLE  (student_topic_progress_report)
# ============================================================


class StudentTopicProgressReport(Base):
    __tablename__ = "student_topic_progress_report"

    topic_progress_report_code = Column(String(30), primary_key=True, default=generate_uuid)

    report_id = Column(
        String(30),
        ForeignKey("student_report.report_code"),
        nullable=False,
        index=True,
    )

    topic_id = Column(
        String(30),
        ForeignKey("ka_topic.topic_code"),
        nullable=False,
        index=True,
    )

    topic_progress_id = Column(
        String(30),
        ForeignKey("ka_topic_progress.topic_progress_code"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------
    # "StudentReport" is package se bahar defined maana gaya hai.

    report = relationship("StudentReport", lazy="joined")

    topic = relationship("Topic", back_populates="report_links", lazy="joined")

    topic_progress = relationship(
        "TopicProgress",
        back_populates="report_links",
        lazy="joined",
    )

    __table_args__ = (
        Index("idx_student_topic_report_report", "report_id"),
        Index("idx_student_topic_report_topic", "topic_id"),
        Index("idx_student_topic_report_progress", "topic_progress_id"),
    )
