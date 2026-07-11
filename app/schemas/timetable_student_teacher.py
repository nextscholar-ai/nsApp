from datetime import time
from typing import Optional
from pydantic import BaseModel


# Student timetable response (required fields)
class StudentTimetableItemResponse(BaseModel):
    day: str
    start_time: time
    end_time: time
    subject: str
    teacher: str


# Teacher timetable response (required fields)
class TeacherTimetableItemResponse(BaseModel):
    class_: str
    subject: str
    day: str
    time: str

    # Allow the API field name to be `class` while keeping
    # Python attribute name as `class_`.
    def model_dump(self, *args, **kwargs):  # pragma: no cover
        data = super().model_dump(*args, **kwargs)
        if "class_" in data:
            data["class"] = data.pop("class_")
        return data

