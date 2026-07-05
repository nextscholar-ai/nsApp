import uuid
import secrets

from sqlalchemy import Enum as SAEnum

from datetime import datetime
from app.core.constants import *
from app.core.enums import *
from app.core.mixins import *
from app.helpers.code_generators import *
from app.helpers.validators import Validators
from app.helpers.date_utils import DateUtils
from app.helpers.security import SecurityUtils


from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    Time,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    Numeric

)

from sqlalchemy.orm import (
    relationship,
    declared_attr
)

from app.api.database import Base


# ============================================================
# AUTO TABLENAME
# ============================================================


# ============================================================
# USER TABLE
# ============================================================

class User(

    Base,

    TimestampMixin,

    ActiveMixin,

    AuditMixin,

    SoftDeleteMixin

):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # ------------------------------------------------
    # BUSINESS IDS
    # ------------------------------------------------

    admin_id = Column(
        String(MAX_CODE_LENGTH),
        unique=True,
        nullable=True,
        index=True
    )

    teacher_id = Column(
        String(MAX_CODE_LENGTH),
        unique=True,
        nullable=True,
        index=True
    )

    student_id = Column(
        String(MAX_CODE_LENGTH),
        unique=True,
        nullable=True,
        index=True
    )

    # ------------------------------------------------
    # LOGIN
    # ------------------------------------------------

    email = Column(
        String(MAX_EMAIL_LENGTH),
        unique=True,
        nullable=False,
        index=True
    )

    phone = Column(
        String(MAX_PHONE_LENGTH),
        unique=False,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        SAEnum(UserRole),
        nullable=False,
        index=True
    )

    profile_photo = Column(
        String(MAX_FILE_PATH),
        nullable=True
    )

    last_seen = Column(
        DateTime,
        nullable=True
    )

    device_token = Column(
        String(255),
        nullable=True
    )

    # ------------------------------------------------
    # EMAIL OTP LOGIN
    # ------------------------------------------------

    email_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )

    email_otp = Column(
        String(6),
        nullable=True
    )

    email_otp_expiry = Column(
        DateTime,
        nullable=True
    )

    # ------------------------------------------------
    # SECURITY
    # ------------------------------------------------

    last_login = Column(
        DateTime,
        nullable=True
    )

    login_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    failed_login_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    password_changed_at = Column(
        DateTime,
        nullable=True
    )

    last_password_reset = Column(
        DateTime,
        nullable=True
    )

    # ------------------------------------------------
    # TABLE CONSTRAINTS
    # ------------------------------------------------

    __table_args__ = (

        CheckConstraint(

            role.in_(

                [
                    ROLE_ADMIN,
                    ROLE_TEACHER,
                    ROLE_STUDENT
                ]

            ),

            name="ck_user_role"

        ),

        Index(
            "idx_user_role_active",
            "role",
            "is_active"
        ),

        Index(
            "idx_user_email_active",
            "email",
            "is_active"
        ),

        Index(
            "idx_user_phone_active",
            "phone",
            "is_active"
        )

    )

    # ===============================
    # PROFILE RELATIONSHIPS
    # ===============================

    student_profile = relationship(
        "StudentProfile",
        foreign_keys="StudentProfile.user_id",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    teacher_profile = relationship(
        "TeacherProfile",
        foreign_keys="TeacherProfile.user_id",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    admin_profile = relationship(
        "AdminProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Missing: User to created/updated relationships
    created_classes = relationship("ClassRoom", foreign_keys="ClassRoom.created_by", back_populates="creator")
    updated_classes = relationship("ClassRoom", foreign_keys="ClassRoom.updated_by", back_populates="updater")
    created_subjects = relationship("Subject", foreign_keys="Subject.created_by", back_populates="creator")
    updated_subjects = relationship("Subject", foreign_keys="Subject.updated_by", back_populates="updater")


# ============================================================
# STUDENTPROFILE TABLE
# ============================================================

class StudentProfile(

    Base,

    TimestampMixin,

    ActiveMixin,

    AuditMixin

):

    __tablename__ = "student_profiles"

    # ------------------------------------------------
    # PRIMARY KEY
    # ------------------------------------------------

    student_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("users.student_id"),
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )

    # ------------------------------------------------
    # BASIC DETAILS
    # ------------------------------------------------

    admission_number = Column(
        String(30),
        unique=True,
        nullable=True,
        index=True
    )

    student_name = Column(
        String(MAX_NAME_LENGTH),
        nullable=False
    )

    gender = Column(
        String(20),
        nullable=True
    )

    date_of_birth = Column(
        Date,
        nullable=True
    )

    blood_group = Column(
        String(10),
        nullable=True
    )

    profile_photo = Column(
        String(MAX_FILE_PATH),
        nullable=True
    )

    school_name = Column(
        String(255),
        nullable=False
    )

    school_address = Column(
        Text,
        nullable=True
    )

    medium = Column(
        String(100),
        nullable=True
    )

    board = Column(
        String(100),
        nullable=True
    )


    # ------------------------------------------------
    # CONTACT
    # ------------------------------------------------

    address = Column(
        Text,
        nullable=True
    )

    city = Column(
        String(100),
        nullable=True
    )

    state = Column(
        String(100),
        nullable=True
    )

    pincode = Column(
        String(10),
        nullable=True
    )

    # ------------------------------------------------
    # PARENT DETAILS
    # ------------------------------------------------

    parent_name = Column(
        String(MAX_NAME_LENGTH),
        nullable=True
    )

    parent_phone = Column(
        String(MAX_PHONE_LENGTH),
        nullable=True
    )

    guardian_name = Column(
        String(MAX_NAME_LENGTH),
        nullable=True
    )

    guardian_phone = Column(
        String(MAX_PHONE_LENGTH),
        nullable=True
    )

    emergency_contact = Column(
        String(MAX_PHONE_LENGTH),
        nullable=True
    )

    # ------------------------------------------------
    # STATUS
    # ------------------------------------------------

    admission_date = Column(
        Date,
        nullable=True
    )

    remarks = Column(
        Text,
        nullable=True
    )

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------


    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="student_profile"
    )

    student_class = relationship(
        "StudentClass",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    promotion_history = relationship(
        "StudentPromotionHistory",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    

    # ------------------------------------------------
    # TABLE SETTINGS
    # ------------------------------------------------

    __table_args__ = (

        Index(
            "idx_student_id",
            "student_id"
        ),
    )


# ============================================================
# TEACHERPROFILE TABLE
# ============================================================

class TeacherProfile(

    Base,

    TimestampMixin,

    ActiveMixin,

    AuditMixin

):

    __tablename__ = "teacher_profiles"

    # ------------------------------------------------
    # PRIMARY KEY
    # ------------------------------------------------

    teacher_id = Column(
        String(MAX_CODE_LENGTH),
        ForeignKey("users.teacher_id"),
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )

    # ------------------------------------------------
    # BASIC DETAILS
    # ------------------------------------------------

    teacher_name = Column(
        String(MAX_NAME_LENGTH),
        nullable=False
    )

    gender = Column(
        String(20),
        nullable=True
    )

    date_of_birth = Column(
        Date,
        nullable=True
    )

    qualification = Column(
        String(255),
        nullable=True
    )

    experience_years = Column(
        Float,
        default=0,
        nullable=True
    )

    specialization = Column(
        String(255),
        nullable=True
    )

    profile_photo = Column(
        String(MAX_FILE_PATH),
        nullable=True
    )

    # ------------------------------------------------
    # EMPLOYMENT
    # ------------------------------------------------

    employee_code = Column(
        String(30),
        unique=True,
        nullable=True,
        index=True
    )

    joining_date = Column(
        Date,
        nullable=True
    )

    designation = Column(
        String(100),
        nullable=True
    )

    department = Column(
        String(100),
        nullable=True
    )

    # ------------------------------------------------
    # CONTACT
    # ------------------------------------------------

    address = Column(
        Text,
        nullable=True
    )

    city = Column(
        String(100),
        nullable=True
    )

    state = Column(
        String(100),
        nullable=True
    )

    pincode = Column(
        String(10),
        nullable=True
    )

    emergency_contact = Column(
        String(MAX_PHONE_LENGTH),
        nullable=True
    )

    # ------------------------------------------------
    # STATUS
    # ------------------------------------------------

    remarks = Column(
        Text,
        nullable=True
    )

    # ------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------

    

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="teacher_profile"
    )

    class_teacher_of = relationship(
        "ClassRoom",
        foreign_keys="ClassRoom.class_teacher_id",
        back_populates="class_teacher"
    )

    teacher_subjects = relationship(
      "TeacherSubject",
        back_populates="teacher",
        cascade="all, delete-orphan"
    )




    # ------------------------------------------------
    # INDEXES
    # ------------------------------------------------

    __table_args__ = (

        Index(
            "idx_teacher_department",
            "department"
        ),

        Index(
            "idx_teacher_employee",
            "employee_code"
        ),

    )


# ============================================================
# ADMINPROFILE TABLE
# ============================================================

class AdminProfile(
    Base,
    TimestampMixin,
    ActiveMixin,
    AuditMixin
):
    __tablename__ = "admin_profiles"

    # ======================================================
    # Primary Key
    # ======================================================

    admin_id = Column(
        String(30),
        primary_key=True,
        default=generate_admin_code,
        index=True
    )

    # ======================================================
    # User Relation
    # ======================================================

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False,
        index=True
    )

    # ======================================================
    # Basic Details
    # ======================================================

    admin_name = Column(
        String(120),
        nullable=False
    )

    designation = Column(
        String(100),
        nullable=True
    )

    phone = Column(
        String(20),
        nullable=True
    )

    profile_photo = Column(
        String(300),
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    # ======================================================
    # Permissions
    # ======================================================

    can_create_admin = Column(
        Boolean,
        default=False,
        nullable=False
    )

    super_admin = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # ======================================================
    # Relationships
    # ======================================================

    user = relationship(
        "User",
        back_populates="admin_profile"
    )

    # ======================================================
    # Constraints
    # ======================================================

    __table_args__ = (

        UniqueConstraint(
            "user_id",
            name="uq_admin_user"
        ),

        Index(
            "idx_admin_id",
            "admin_id"
        ),

    )


