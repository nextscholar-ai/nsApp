import datetime

from .common import BaseSchema


class TopicBase(BaseSchema):
    course_id: str | None = None
    topic_id: str | None = None
    topic_name: str | None = None


class TopicCreate(BaseSchema):
    course_id: str | None = None
    topic_id: str
    topic_name: str | None = None


class TopicResponse(TopicBase):
    topic_code: str


class TopicProgressBase(BaseSchema):
    student_id: str
    course_id: str | None = None
    topic_id: str
    point_available: int | None = None
    point_earned: int | None = None
    percentage_earned: int | None = None
    date: datetime.date | None = None


class TopicProgressCreate(BaseSchema):
    student_id: str
    course_id: str | None = None
    topic_id: str
    point_available: int | None = None
    point_earned: int | None = None
    percentage_earned: int | None = None
    date: datetime.date | None = None


class TopicProgressResponse(TopicProgressBase):
    topic_progress_code: str
    topic_progress_id: str | None = None


class StudentTopicProgressReportBase(BaseSchema):
    report_id: str
    topic_id: str
    topic_progress_id: str


class StudentTopicProgressReportCreate(BaseSchema):
    report_id: str
    topic_id: str
    topic_progress_id: str


class StudentTopicProgressReportResponse(StudentTopicProgressReportBase):
    topic_progress_report_code: str
