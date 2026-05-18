import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt as pyjwt

from src.settings import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _make_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra: dict = None,
) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    token = pyjwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        headers={"kid": "default"},
    )
    return token, jti


def create_access_token(user_id: int, username: str) -> tuple[str, str, datetime]:
    delta = timedelta(minutes=settings.access_token_expire_minutes)
    token, jti = _make_token(str(user_id), "access", delta, {"username": username})
    return token, jti, datetime.now(timezone.utc) + delta


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    delta = timedelta(days=settings.refresh_token_expire_days)
    token, jti = _make_token(str(user_id), "refresh", delta)
    return token, jti, datetime.now(timezone.utc) + delta


def decode_token(token: str) -> Optional[dict]:
    try:
        return pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except pyjwt.InvalidTokenError:
        return None