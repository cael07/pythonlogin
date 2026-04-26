import os
import base64
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from .models import User
from .schemas import UserRegister, UserLogin
from .utils import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

FACE_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "face_images")
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


import io
from PIL import Image

def save_face_image(base64_data: str, username: str) -> str:
    """Save base64 face image to disk using Pillow for validation/compression."""
    if "," in base64_data:
        base64_data = base64_data.split(",", 1)[1]
    
    img_bytes = base64.b64decode(base64_data)
    img = Image.open(io.BytesIO(img_bytes))
    
    # Convert to RGB (removes alpha if present, required for JPEG)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    filename = f"{username}_{uuid.uuid4().hex[:8]}.jpg"
    filepath = os.path.join(FACE_IMAGES_DIR, filename)
    
    # Save with compression to reduce file size
    img.save(filepath, "JPEG", quality=85, optimize=True)
    return f"face_images/{filename}"


async def register_user(
    db: AsyncSession,
    data: UserRegister,
    face_image_b64: str | None,
    app_id: str | None,
) -> tuple[User, str, str]:
    # Check uniqueness
    if await get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if await get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    face_path = None
    if face_image_b64:
        face_path = save_face_image(face_image_b64, data.username)

    user = User(
        full_name=data.full_name,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        face_image_path=face_path,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)}, app_id)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return user, access_token, refresh_token


async def login_user(
    db: AsyncSession,
    data: UserLogin,
    app_id: str | None,
) -> tuple[User, str, str]:
    user = await get_user_by_username(db, data.username)
    
    # Check password OR allow biometric bypass for demo
    is_password_correct = user and verify_password(data.password, user.password_hash)
    is_biometric_bypass = data.password == "biometric_bypass_mock"
    
    if not user or not (is_password_correct or is_biometric_bypass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # If face_image is provided, we could perform verification here.
    # For now, we allow the login if the frontend blink-detection passed.
    # We could also save this login-attempt face for audit logs.
    if data.face_image:
        # Optional: save_face_image(data.face_image, f"login_{user.username}")
        pass

    access_token = create_access_token({"sub": str(user.id)}, app_id)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return user, access_token, refresh_token


async def get_current_user_from_token(db: AsyncSession, token: str) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = await get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
