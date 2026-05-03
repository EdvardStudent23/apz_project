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
    for entry in jwks.get("keys", []):
        if entry.get("kid") == kid:
            return RSAAlgorithm.from_jwk(entry)
    return None


async def get_current_user(
    request: Request,
    authorization: str | None = Header(None),
) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    jwks = getattr(request.app.state, "jwks", None)
    if not jwks:
        raise HTTPException(status_code=500, detail="JWKS not initialized")

    try:
        payload = verify_jwt(token, jwks)
        return UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
