# app/helpers/code_generators.py

import uuid
import secrets
import string
from datetime import datetime

from app.core.constants import (
    STUDENT_PREFIX, TEACHER_PREFIX, ADMIN_PREFIX, MATERIAL_PREFIX,
    NOTICE_PREFIX, ASSIGNMENT_PREFIX, EXAM_PREFIX,
    FEE_PREFIX, RECEIPT_PREFIX, CHAT_PREFIX,
    TIMETABLE_PREFIX, AVAILABILITY_PREFIX
)

def generate_uuid():
    return str(uuid.uuid4())

def random_code(length: int = 6):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def generate_student_id(user_id: int):
    return f"{STUDENT_PREFIX}{user_id:05d}"

def generate_teacher_id(user_id: int):
    return f"{TEACHER_PREFIX}{user_id:05d}"

def generate_admin_id(user_id: int):
    return f"{ADMIN_PREFIX}{user_id:06d}"


# ------------------------------------------------------------
# No-arg generators for use as SQLAlchemy Column(default=...)
# (the row's own id/user_id isn't known yet at insert time,
# so these use a random suffix instead)
# ------------------------------------------------------------

def generate_admin_code():
    return f"{ADMIN_PREFIX}-{random_code(8)}"


def generate_assignment_id():
    return f"{ASSIGNMENT_PREFIX}-{random_code(8)}"


def generate_material_id():
    return f"{MATERIAL_PREFIX}-{random_code(8)}"

def generate_notice_code():
    return f"{NOTICE_PREFIX}-{random_code(8)}"

def generate_assignment_code():
    return f"{ASSIGNMENT_PREFIX}-{random_code(8)}"

def generate_exam_code():
    return f"{EXAM_PREFIX}-{random_code(8)}"

def generate_fee_code():
    return f"{FEE_PREFIX}-{random_code(8)}"

def generate_receipt_no():
    return f"{RECEIPT_PREFIX}-{random_code(10)}"

def generate_chat_room_id():
    return f"{CHAT_PREFIX}-{random_code(8)}"

def generate_timetable_id(academic_sessions_id: int, sequence: int):
    return f"{TIMETABLE_PREFIX}-{academic_sessions_id}-{sequence:06d}"

def generate_availability_id(academic_sessions_id: int, sequence: int):
    return f"{AVAILABILITY_PREFIX}-{academic_sessions_id}-{sequence:06d}"

def generate_session_name(start_year: int, end_year: int):
    return f"{start_year}-{str(end_year)[-2:]}"

def generate_subject_code(subject_name: str, class_name: str):
    words = subject_name.upper().split()
    if len(words) == 1:
        prefix = words[0][:2]
    else:
        prefix = "".join(word[0] for word in words)[:2]
    digits = "".join(filter(str.isdigit, class_name))
    return f"{prefix}{digits}"