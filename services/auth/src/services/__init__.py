from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import User, redis_manager
from src.settings import settings
from src.services.jwt import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.services.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AccountDisabledError,
    InvalidTokenError,
    SessionExpiredError,
)
from src.routes.schemas import RegisterRequest, LoginRequest, TokenResponse


class AuthService:

    # ------------------------------------------------------------------ #
    #  Register                                                            #
    # ------------------------------------------------------------------ #

    async def register(
        self, data: RegisterRequest, db: AsyncSession
    ) -> tuple[User, TokenResponse]:
        if await db.scalar(select(User).where(User.username == data.username)):
            raise UserAlreadyExistsError("username")

        if await db.scalar(select(User).where(User.email == data.email)):
            raise UserAlreadyExistsError("email")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        tokens = await self._issue_tokens(user)
        return user, tokens

    # ------------------------------------------------------------------ #
    #  Login                                                               #
    # ------------------------------------------------------------------ #

    async def login(
        self, data: LoginRequest, db: AsyncSession
    ) -> tuple[User, TokenResponse]:
        user = await db.scalar(
            select(User).where(
                (User.username == data.username) | (User.email == data.username)
            )
        )

        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountDisabledError()

        tokens = await self._issue_tokens(user)
        return user, tokens

    # ------------------------------------------------------------------ #
    #  Logout                                                              #
    # ------------------------------------------------------------------ #

    async def logout(self, token: str, all_devices: bool = False) -> None:
        payload = decode_token(token)
        if not payload:
            raise InvalidTokenError()

        user_id = int(payload["sub"])
        jti = payload["jti"]

        if all_devices:
            await redis_manager.delete_all_user_sessions(user_id)
        else:
            await redis_manager.delete_session(user_id, jti, "access")
            ttl = self._remaining_ttl(payload)
            if ttl > 0:
                await redis_manager.blacklist_token(jti, ttl)

    # ------------------------------------------------------------------ #
    #  Refresh                                                             #
    # ------------------------------------------------------------------ #

    async def refresh(self, refresh_token: str, db: AsyncSession) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid refresh token")

        user_id = int(payload["sub"])
        jti = payload["jti"]

        session = await redis_manager.get_session(user_id, jti, "refresh")
        if not session:
            raise SessionExpiredError()

        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise AccountDisabledError()

        await redis_manager.delete_session(user_id, jti, "refresh")
        return await self._issue_tokens(user)

    # ------------------------------------------------------------------ #
    #  Validate (для інших мікросервісів)                                  #
    # ------------------------------------------------------------------ #

    async def validate_token(self, token: str) -> Optional[dict]:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None

        user_id = int(payload["sub"])
        jti = payload["jti"]

        if await redis_manager.is_token_blacklisted(jti):
            return None

        session = await redis_manager.get_session(user_id, jti, "access")
        if not session:
            return None

        return {"user_id": user_id, "username": payload.get("username"), "jti": jti}

    # ------------------------------------------------------------------ #
    #  Private                                                             #
    # ------------------------------------------------------------------ #

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token, access_jti, access_exp = create_access_token(user.id, user.username)
        refresh_token, refresh_jti, _ = create_refresh_token(user.id)

        await redis_manager.save_session(
            user_id=user.id,
            jti=access_jti,
            token_type="access",
            ttl_seconds=settings.access_token_expire_minutes * 60,
            extra={"username": user.username},
        )
        await redis_manager.save_session(
            user_id=user.id,
            jti=refresh_jti,
            token_type="refresh",
            ttl_seconds=settings.refresh_token_expire_days * 24 * 3600,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=access_exp,
        )

    @staticmethod
    def _remaining_ttl(payload: dict) -> int:
        exp = payload.get("exp")
        if not exp:
            return 0
        return max(0, int(exp - datetime.now(timezone.utc).timestamp()))


auth_service = AuthService()
