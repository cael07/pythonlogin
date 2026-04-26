from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from ..database import get_db
from . import service
from .schemas import UserRegister, RegisterRequest, UserLogin, TokenPair, UserOut, RefreshRequest, MessageResponse
from .utils import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenPair)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    user, access, refresh = service.register_user(
        db, request.user, request.face_image, request.app_id
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user
    }

@router.post("/login", response_model=TokenPair)
def login(
    credentials: UserLogin,
    app_id: str | None = None,
    db: Session = Depends(get_db)
):
    user, access, refresh = service.login_user(db, credentials, app_id)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user
    }

@router.get("/me", response_model=UserOut)
def get_me(
    token: str = Depends(lambda x: x), # Simplified for brevity, usually use OAuth2PasswordBearer
    db: Session = Depends(get_db)
):
    # This is a placeholder; real implementation would extract token from header
    pass

@router.post("/refresh")
def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    from .utils import decode_token
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    user = service.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    new_access = create_access_token({"sub": str(user.id)})
    return {"access_token": new_access}

@router.get("/health")
def health():
    from ..database import check_db_health
    db_ok = check_db_health()
    return {
        "status": "ok",
        "database": "online" if db_ok else "offline",
        "service": "pythonlogin-auth"
    }
