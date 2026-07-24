from sqlalchemy import Column, String

from app.api.database import Base
from app.helpers.code_generators import generate_ka_course_code


class KaCourse(Base):
    __tablename__ = "ka_course"

    ka_course_code = Column(String(30), primary_key=True, default=generate_ka_course_code)
    course_name = Column(String(200), nullable=True)
    course_id = Column(String(100), unique=True, nullable=True)
