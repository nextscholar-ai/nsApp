import os
import random
from datetime import UTC, datetime, timedelta

import bcrypt
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
from jose import JWTError, jwt

# =========================
# CONFIG
# =========================


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


# =========================
# PASSWORD HASH
# =========================


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# =========================
# JWT TOKEN
# =========================


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload if "sub" in payload else None
    except JWTError:
        return None


def verify_access_token(token: str):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if "sub" not in payload:
            return None

        if "role" not in payload:
            return None

        return payload

    except JWTError:
        return None


def create_auth_tokens(user_id: str, role: str):
    payload = {"sub": str(user_id), "role": role}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    return {"access_token": access_token, "refresh_token": refresh_token}


# =========================
# RESET TOKEN
# =========================

serializer = URLSafeTimedSerializer(SECRET_KEY)


def create_reset_token(email: str):
    return serializer.dumps(email, salt="reset-password")


def verify_reset_token(token: str, max_age=1800):
    try:
        return serializer.loads(token, salt="reset-password", max_age=max_age)
    except Exception:
        return None


# =========================
# OTP
# =========================


def generate_otp(length: int = 6):
    digits = "0123456789"
    return "".join(random.choice(digits) for _ in range(length))  # noqa: S311
