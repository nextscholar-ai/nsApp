# ============================================================
# services/auth_service.py - Authentication Service
# ============================================================

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    generate_otp,
    hash_password,
    verify_access_token,
    verify_password,
    verify_refresh_token,
    verify_reset_token,
)
from app.core.enums import UserRole
from app.model import User
from app.repositories.core_repositories import (
    AdminProfileRepository,
    StudentProfileRepository,
    TeacherProfileRepository,
    UserRepository,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.student_repo = StudentProfileRepository(db)
        self.teacher_repo = TeacherProfileRepository(db)
        self.admin_repo = AdminProfileRepository(db)

    def authenticate_user(self, identifier: str, password: str) -> User | None:
        user = self.user_repo.get_by_identifier(identifier)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            self.user_repo.increment_failed_login(user.id)
            return None
        if not user.is_active or user.is_deleted:
            return None
        self.user_repo.update_last_login(user.id)
        return user

    def authenticate_with_otp(self, email: str, otp: str) -> User | None:
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if not self.user_repo.verify_otp(user.id, otp):
            return None
        self.user_repo.clear_otp(user.id)
        self.user_repo.update_last_login(user.id)
        return user

    def create_tokens(self, user: User) -> dict[str, str]:
        token_data = {"sub": str(user.id), "role": user.role.value}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, str] | None:
        payload = verify_refresh_token(refresh_token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active or user.is_deleted:
            return None
        return {
            "access_token": create_access_token(
                {"sub": str(user.id), "role": user.role.value},
            ),
        }

    def verify_token(self, token: str) -> dict[str, Any] | None:
        payload = verify_access_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active or user.is_deleted:
            return None
        return {"user": user, "payload": payload}

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
        if not verify_password(current_password, user.password_hash):
            return False
        self.user_repo.update_password(user_id, hash_password(new_password))
        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        email = verify_reset_token(token)
        if not email:
            return False
        user = self.user_repo.get_by_email(email)
        if not user:
            return False
        self.user_repo.update_password(user.id, hash_password(new_password))
        return True

    def send_reset_token(self, email: str) -> str | None:
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        return create_reset_token(email)

    def send_verification_otp(self, email: str) -> bool:
        user = self.user_repo.get_by_email(email)
        if not user or user.email_verified:
            return False
        otp = generate_otp(6)
        self.user_repo.set_otp(user.id, otp)
        logger.info("OTP for %s: %s", email, otp)
        return True

    def verify_email(self, email: str, otp: str) -> bool:
        user = self.user_repo.get_by_email(email)
        if not user or user.email_verified:
            return False
        if not self.user_repo.verify_otp(user.id, otp):
            return False
        self.user_repo.verify_email(user.id)
        return True

    def get_user_with_profiles(self, user_id: int) -> dict[str, Any]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"user": None}

        result = {"user": user}
        if user.role == UserRole.STUDENT:
            result["profile"] = self.student_repo.get_by_user_id(user.id)
        elif user.role == UserRole.TEACHER:
            result["profile"] = self.teacher_repo.get_by_user_id(user.id)
        elif user.role == UserRole.ADMIN:
            result["profile"] = self.admin_repo.get_by_user_id(user.id)
        return result
