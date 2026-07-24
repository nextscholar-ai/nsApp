from sqlalchemy import Column, DateTime, String

from app.api.database import Base
from app.helpers.code_generators import generate_report_code


class StudentReport(Base):
    __tablename__ = "student_report"

    report_code = Column(
        String(30),
        primary_key=True,
        default=generate_report_code,
    )
    student_id = Column(String(50), nullable=True)
    report_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True)
