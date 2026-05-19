from __future__ import annotations

from typing import Any
from uuid import UUID

import jwt as pyjwt
from fastapi import Header, HTTPException, Request
from jwt.algorithms import RSAAlgorithm


class InvalidTokenError(Exception):
    pass


def verify_jwt(token: str, jwks: dict[str, Any], audience: str | None = None) -> dict[str, Any]:
    try:
        header = pyjwt.get_unverified_header(token)
    except pyjwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    kid = header.get("kid")
    key = _key_for(jwks, kid)
    if key is None:
        raise InvalidTokenError(f"no JWKS entry for kid={kid!r}")

    try:
        return pyjwt.decode(
            token,
            key=key,
            algorithms=[header.get("alg", "RS256")],
            audience=audience,
        )
    except pyjwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc


def _key_for(jwks: dict[str, Any], kid: str | None) -> Any:
    import base64
    for entry in jwks.get("keys", []):
        if entry.get("kid") == kid:
            kty = entry.get("kty")
            if kty == "oct":
                k = entry.get("k")
                # Add padding if needed
                padding = 4 - (len(k) % 4)
                if padding != 4:
                    k += "=" * padding
                return base64.urlsafe_b64decode(k)
            elif kty == "RSA":
                return RSAAlgorithm.from_jwk(entry)
    return None


def _decode_request_token(request: Request, authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    jwks = getattr(request.app.state, "jwks", None)
    if not jwks:
        raise HTTPException(status_code=500, detail="JWKS not initialized")

    try:
        return verify_jwt(token, jwks)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


def _sub_to_uuid(sub: Any) -> UUID:
    try:
        return UUID(str(sub))
    except ValueError:
        return UUID(int=int(sub))


class CurrentUser:
    """JWT-derived identity for downstream services.

    `id` is the canonical UUID used across services (derived from the integer
    auth subject via `_sub_to_uuid`). `is_admin` reflects the claim set by
    the auth service; defaults to False on older tokens.
    """

    __slots__ = ("id", "raw_sub", "is_admin", "username")

    def __init__(self, id: UUID, raw_sub: str, is_admin: bool, username: str | None) -> None:
        self.id = id
        self.raw_sub = raw_sub
        self.is_admin = is_admin
        self.username = username


async def get_current_user(
    request: Request,
    authorization: str | None = Header(None),
) -> UUID:
    payload = _decode_request_token(request, authorization)
    try:
        return _sub_to_uuid(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))


async def get_current_identity(
    request: Request,
    authorization: str | None = Header(None),
) -> CurrentUser:
    payload = _decode_request_token(request, authorization)
    try:
        sub = payload["sub"]
    except KeyError:
        raise HTTPException(status_code=401, detail="Token missing subject")
    try:
        uid = _sub_to_uuid(sub)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return CurrentUser(
        id=uid,
        raw_sub=str(sub),
        is_admin=bool(payload.get("is_admin", False)),
        username=payload.get("username"),
    )


async def require_admin(
    request: Request,
    authorization: str | None = Header(None),
) -> CurrentUser:
    user = await get_current_identity(request, authorization)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privilege required")
    return user
