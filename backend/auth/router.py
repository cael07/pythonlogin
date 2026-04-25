from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from . import schemas, service
from .utils import decode_token, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.TokenPair, status_code=201)
async def register(body: schemas.RegisterRequest, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await service.register_user(
        db, body.user, body.face_image, body.app_id
    )
    return schemas.TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/login", response_model=schemas.TokenPair)
async def login(
    body: schemas.UserLogin,
    app_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, refresh_token = await service.login_user(db, body, app_id)
    return schemas.TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=schemas.TokenPair)
async def refresh_token_endpoint(
    body: schemas.RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    user = await service.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    new_access = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})
    return schemas.TokenPair(
        access_token=new_access,
        refresh_token=new_refresh,
        user=schemas.UserOut.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserOut)
async def get_me(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[7:]
    user = await service.get_current_user_from_token(db, token)
    return schemas.UserOut.model_validate(user)


@router.get("/health")
async def health():
    return {"status": "ok", "service": "pythonlogin-auth"}
