import base64
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db, User
from src.services import auth_service
from src.settings import settings
from src.routes.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    AuthResponse,
    TokenResponse,
    UserResponse,
    UserLookupResponse,
    MessageResponse,
)
from src.routes.dependencies import get_current_user, get_bearer_token

router = APIRouter(tags=["auth"])


@router.get("/.well-known/jwks.json")
async def get_jwks():
    """Export JWT public key in JWKS format for token verification."""
    if settings.jwt_algorithm == "HS256":
        key_bytes = settings.jwt_secret_key.encode()
        key_b64 = base64.urlsafe_b64encode(key_bytes).decode().rstrip("=")
        return {
            "keys": [
                {
                    "kty": "oct",
                    "k": key_b64,
                    "kid": "default",
                    "alg": "HS256",
                }
            ]
        }
    return {"keys": []}


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=AuthResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await auth_service.register(data, db)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@auth_router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await auth_service.login(data, db)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    all_devices: bool = Query(default=False),
    token: str = Depends(get_bearer_token),
):
    await auth_service.logout(token, all_devices=all_devices)
    msg = "Logged out from all devices" if all_devices else "Successfully logged out"
    return MessageResponse(message=msg)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh(data.refresh_token, db)


@auth_router.get("/validate")
async def validate(current_user: dict = Depends(get_current_user)):
    return {"valid": True, "user": current_user}


@auth_router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, current_user["user_id"])
    return UserResponse.model_validate(user)


@auth_router.get("/users/lookup", response_model=UserLookupResponse)
async def lookup_user(
    email: str | None = Query(default=None),
    username: str | None = Query(default=None),
    _: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a recipient for a payment flow.

    Authenticated to prevent unauthenticated email/username enumeration.
    Returns only the public-safe slice (id + username) — never the email,
    even when looked up by it.
    """
    if not email and not username:
        raise HTTPException(status_code=400, detail="email or username is required")

    needle = (email or username or "").strip().lower()
    if not needle:
        raise HTTPException(status_code=400, detail="email or username is required")

    column = User.email if email else User.username
    user = await db.scalar(select(User).where(column == needle))
    if not user:
        raise HTTPException(status_code=404, detail="No user matches that email")
    if not user.is_active:
        raise HTTPException(status_code=404, detail="No user matches that email")

    return UserLookupResponse(id=user.id, username=user.username)


router.include_router(auth_router)
