# app/core/enums.py

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class Gender(StrEnum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class UserStatus(StrEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BLOCKED = "Blocked"


class AssignmentStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    DELETED = "DELETED"


class ExamStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class FeeStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class NoticeType(StrEnum):
    GENERAL = "GENERAL"
    ACADEMIC = "ACADEMIC"
    EXAM = "EXAM"
    FEE = "FEE"
    EVENT = "EVENT"


class NoticeAudience(StrEnum):
    ALL = "ALL"
    CLASS = "CLASS"
    SECTION = "SECTION"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class MaterialType(StrEnum):
    PDF = "PDF"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    LINK = "LINK"
    OTHER = "OTHER"


class AttendanceStatus(StrEnum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    LEAVE = "Leave"
    HOLIDAY = "Holiday"


class PromotionType(StrEnum):
    PROMOTED = "PROMOTED"
    RETAINED = "RETAINED"
    TRANSFERRED = "TRANSFERRED"


class LectureStatus(StrEnum):
    SCHEDULED = "Scheduled"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
