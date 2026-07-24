# ============================================================
# repositories/user_repository.py - User Repository
# ============================================================

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.model import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with specialized methods."""

    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email.lower().strip()).first()

    def get_by_phone(self, phone: str) -> User | None:
        """Get user by phone."""
        return self.db.query(User).filter(User.phone == phone).first()

    def get_by_identifier(self, identifier: str) -> User | None:
        """Get user by email or phone."""
        return (
            self.db.query(User)
            .filter(
                or_(
                    User.email == identifier.lower().strip(),
                    User.phone == identifier.strip(),
                ),
            )
            .first()
        )

    def get_by_student_id(self, student_id: str) -> User | None:
        """Get user by student ID."""
        return self.db.query(User).filter(User.student_id == student_id).first()

    def get_by_teacher_id(self, teacher_id: str) -> User | None:
        """Get user by teacher ID."""
        return self.db.query(User).filter(User.teacher_id == teacher_id).first()

    def get_by_admin_id(self, admin_id: str) -> User | None:
        """Get user by admin ID."""
        return self.db.query(User).filter(User.admin_id == admin_id).first()

    def get_active_user(self, role: UserRole | None = None) -> list[User]:
        """Get active user."""
        query = self.db.query(User).filter(User.is_active, not User.is_deleted)
        if role:
            query = query.filter(User.role == role)
        return query.all()

    def get_user_by_role(self, role: UserRole) -> list[User]:
        """Get user by role."""
        return self.db.query(User).filter(User.role == role).all()

    def get_user_by_ids(self, ids: list[int]) -> list[User]:
        """Get user by IDs."""
        return self.db.query(User).filter(User.id.in_(ids)).all()

    def search_user(
        self,
        search: str,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> list[User]:
        """Search user by email or phone."""
        query = self.db.query(User).filter(
            or_(
                User.email.contains(search.lower().strip()),
                User.phone.contains(search.strip()),
            ),
        )

        if role:
            query = query.filter(User.role == role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        return query.all()

    def get_user_with_profiles(self, user_id: int) -> User | None:
        """Get user with all profiles."""
        return self.db.query(User).filter(User.id == user_id).first()

    def update_last_login(self, user_id: int) -> User:
        """Update user's last login timestamp."""
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.now(UTC)
            user.login_count += 1
            user.failed_login_count = 0
            self.db.flush()
        return user

    def increment_failed_login(self, user_id: int) -> User:
        """Increment failed login count."""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_count += 1
            self.db.flush()
        return user

    def reset_failed_login(self, user_id: int) -> User:
        """Reset failed login count."""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_count = 0
            self.db.flush()
        return user

    def update_password(self, user_id: int, password_hash: str) -> User:
        """Update user password."""
        user = self.get_by_id(user_id)
        if user:
            user.password_hash = password_hash
            user.password_changed_at = datetime.now(UTC)
            self.db.flush()
        return user

    def verify_email(self, user_id: int) -> User:
        """Mark email as verified."""
        user = self.get_by_id(user_id)
        if user:
            user.email_verified = True
            user.email_otp = None
            user.email_otp_expiry = None
            self.db.flush()
        return user

    def set_otp(self, user_id: int, otp: str, expiry_minutes: int = 10) -> User:
        """Set OTP for user."""
        from datetime import timedelta

        user = self.get_by_id(user_id)
        if user:
            user.email_otp = otp
            user.email_otp_expiry = datetime.now(UTC) + timedelta(
                minutes=expiry_minutes,
            )
            self.db.flush()
        return user

    def clear_otp(self, user_id: int) -> User:
        """Clear OTP for user."""
        user = self.get_by_id(user_id)
        if user:
            user.email_otp = None
            user.email_otp_expiry = None
            self.db.flush()
        return user

    def verify_otp(self, user_id: int, otp: str) -> bool:
        """Verify user's OTP."""
        user = self.get_by_id(user_id)
        if not user or not user.email_otp:
            return False

        if user.email_otp != otp:
            return False

        return not (user.email_otp_expiry and user.email_otp_expiry < datetime.now(UTC))

    def get_dashboard_stats(self) -> dict[str, Any]:
        """Get user statistics for dashboard."""
        total_user = self.count(is_deleted=False)
        active_user = self.count(is_active=True, is_deleted=False)

        students = self.count(role=UserRole.STUDENT, is_deleted=False)
        teachers = self.count(role=UserRole.TEACHER, is_deleted=False)
        admins = self.count(role=UserRole.ADMIN, is_deleted=False)

        return {
            "total_user": total_user,
            "active_user": active_user,
            "students": students,
            "teachers": teachers,
            "admins": admins,
        }
