"""
Authentication Service with JWT and secure password hashing
"""
from datetime import datetime, timedelta
import hashlib
import os
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from backend.app.config import settings


def get_password_hash(password: str) -> str:
    """Hashes a password with bcrypt, with fallback to sha256 salt if bcrypt is unavailable."""
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    except Exception:
        # Fallback salt hashing
        salt_hex = os.urandom(16).hex()
        digest = hashlib.sha256((password + salt_hex).encode("utf-8")).hexdigest()
        return f"sha256${salt_hex}${digest}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against the stored hash."""
    try:
        if hashed_password.startswith("sha256$"):
            _, salt_hex, digest = hashed_password.split("$", 2)
            check = hashlib.sha256((plain_password + salt_hex).encode("utf-8")).hexdigest()
            return check == digest
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
