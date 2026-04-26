from datetime import datetime, timedelta
from typing import Any
from passlib.context import CryptContext
from jose import JWTError, jwt

SECRET_KEY = "change-this-secret-in-production-use-env-var"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


import hashlib

def hash_password(password: str) -> str:
    # Pre-hash with SHA-256 to bypass Bcrypt's 72-character limit
    # This ensures long passwords work while keeping Bcrypt security
    password_bytes = password.encode('utf-8')
    pre_hashed = hashlib.sha256(password_bytes).hexdigest()
    return pwd_context.hash(pre_hashed)


def verify_password(plain: str, hashed: str) -> bool:
    password_bytes = plain.encode('utf-8')
    pre_hashed = hashlib.sha256(password_bytes).hexdigest()
    return pwd_context.verify(pre_hashed, hashed)


def create_access_token(data: dict[str, Any], app_id: str | None = None) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["type"] = "access"
    if app_id:
        payload["app_id"] = app_id
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload["type"] = "refresh"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return {}
