from __future__ import annotations

from typing import Any

import jwt as pyjwt
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
