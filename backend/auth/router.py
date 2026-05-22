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
    try:
        user, access, refresh = service.register_user(
            db,
            request.user,
            request.face_image,
            request.app_id,
            license_image_b64=request.license_image,
            or_image_b64=request.or_image,
            cr_image_b64=request.cr_image,
        )
        return {
            "access_token": access,
            "refresh_token": refresh,
            "user": user
        }

    except Exception as e:
        import traceback
        print(f"REGISTER ERROR:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

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

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

@router.get("/me", response_model=UserOut)
def get_me(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = service.get_current_user_from_token(db, token)
    return user

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

@router.get("/image/{username}")
def get_user_image(username: str, db: Session = Depends(get_db)):
    user = service.get_user_by_username(db, username)
    if not user or not user.face_image_path:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Path to the actual file
    from .service import FACE_IMAGES_DIR
    file_path = os.path.join(os.path.dirname(FACE_IMAGES_DIR), user.face_image_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    from fastapi.responses import FileResponse
    return FileResponse(file_path, media_type="image/jpeg")

@router.get("/health")
def health():
    from ..database import check_db_health
    db_ok = check_db_health()
    return {
        "status": "ok",
        "database": "online" if db_ok else "offline",
        "service": "pythonlogin-auth"
    }
