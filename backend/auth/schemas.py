from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("username")
    @classmethod
    def username_valid(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores allowed)")
        return v.lower()


class RegisterRequest(BaseModel):
    user: UserRegister
    face_image: Optional[str] = None   # base64 data-URL from camera
    app_id: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str
    face_image: Optional[str] = None


class UserOut(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    face_image_path: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
