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
    # Fail-safe: Force truncate to 71 chars to guarantee it fits in Bcrypt
    safe_password = password[:71]
    return pwd_context.hash(safe_password)


def verify_password(plain: str, hashed: str) -> bool:
    safe_password = plain[:71]
    return pwd_context.verify(safe_password, hashed)


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
