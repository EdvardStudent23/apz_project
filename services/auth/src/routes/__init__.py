from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db, User
from src.services import auth_service
from src.routes.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    AuthResponse,
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from src.routes.dependencies import get_current_user, get_bearer_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await auth_service.register(data, db)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await auth_service.login(data, db)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    all_devices: bool = Query(default=False),
    token: str = Depends(get_bearer_token),
):
    await auth_service.logout(token, all_devices=all_devices)
    msg = "Logged out from all devices" if all_devices else "Successfully logged out"
    return MessageResponse(message=msg)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh(data.refresh_token, db)


@router.get("/validate")
async def validate(current_user: dict = Depends(get_current_user)):
    return {"valid": True, "user": current_user}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, current_user["user_id"])
    return UserResponse.model_validate(user)
