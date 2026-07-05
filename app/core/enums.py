# app/core/enums.py

from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class UserStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BLOCKED = "Blocked"

class AssignmentStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    DELETED = "DELETED"

class ExamStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class FeeStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class NoticeType(str, Enum):
    GENERAL = "GENERAL"
    ACADEMIC = "ACADEMIC"
    EXAM = "EXAM"
    FEE = "FEE"
    EVENT = "EVENT"

class NoticeAudience(str, Enum):
    ALL = "ALL"
    CLASS = "CLASS"
    SECTION = "SECTION"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"

class MaterialType(str, Enum):
    PDF = "PDF"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    LINK = "LINK"
    OTHER = "OTHER"

class AttendanceStatus(str, Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    LEAVE = "Leave"
    HOLIDAY = "Holiday"

class PromotionType(str, Enum):
    PROMOTED = "PROMOTED"
    RETAINED = "RETAINED"
    TRANSFERRED = "TRANSFERRED"

class LectureStatus(str, Enum):
    SCHEDULED = "Scheduled"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"