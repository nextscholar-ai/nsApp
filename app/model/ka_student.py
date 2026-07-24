from sqlalchemy import Column, String

from app.api.database import Base
from app.helpers.code_generators import generate_ka_student_code


class KaStudent(Base):
    __tablename__ = "ka_student"

    ka_student_code = Column(String(30), primary_key=True, default=generate_ka_student_code)
    student_name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
