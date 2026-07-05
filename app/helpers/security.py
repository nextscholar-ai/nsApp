# app/helpers/security.py

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return "".join(secrets.choice("0123456789") for _ in range(length))

    @staticmethod
    def generate_reset_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_otp_expiry(minutes: int = 5) -> datetime:
        return datetime.utcnow() + timedelta(minutes=minutes)