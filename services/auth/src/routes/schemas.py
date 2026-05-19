from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ── Validation constants ────────────────────────────────────────────────────

# Names a user must not be able to take. These are reserved for system
# identities (mailer, automation, etc.) that no human should impersonate.
# NOTE: names eligible for admin promotion via ADMIN_USERNAMES are
# intentionally NOT here — the admin signs up with such a name and gets the
# is_admin flag from settings (see services/__init__.register).
RESERVED_USERNAMES: frozenset[str] = frozenset(
    {
        "root",
        "system",
        "official",
        "nanobank",
        "bank",
        "service",
        "noreply",
        "postmaster",
        "webmaster",
        "abuse",
        "null",
        "undefined",
        "anonymous",
    }
)

# A short stop-list of obviously weak passwords. The point isn't to be
# exhaustive — bcrypt/argon2 cost takes care of brute force — but to reject
# the most embarrassing choices at the API boundary.
COMMON_PASSWORDS: frozenset[str] = frozenset(
    {
        "password",
        "password1",
        "password123",
        "passw0rd",
        "qwerty",
        "qwerty123",
        "letmein",
        "welcome",
        "welcome1",
        "iloveyou",
        "admin123",
        "abc12345",
        "12345678",
        "123456789",
        "1234567890",
        "11111111",
        "00000000",
        "abcd1234",
        "monkey123",
        "dragon123",
        "football",
    }
)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")
USERNAME_LEADING_DIGIT_RE = re.compile(r"^\d")
USERNAME_CONSECUTIVE_UNDERSCORES_RE = re.compile(r"__")
PASSWORD_SPECIAL_RE = re.compile(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]")
PASSWORD_WHITESPACE_RE = re.compile(r"\s")


# --- Requests ---


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalise_username(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not USERNAME_RE.match(v):
            raise ValueError("Username can only contain letters, digits and underscore")
        if USERNAME_LEADING_DIGIT_RE.match(v):
            raise ValueError("Username must not start with a digit")
        if v.startswith("_") or v.endswith("_"):
            raise ValueError("Username must not start or end with an underscore")
        if USERNAME_CONSECUTIVE_UNDERSCORES_RE.search(v):
            raise ValueError("Username must not contain consecutive underscores")
        if v in RESERVED_USERNAMES:
            raise ValueError("This username is reserved, please choose another")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if PASSWORD_WHITESPACE_RE.search(v):
            raise ValueError("Password must not contain whitespace")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not PASSWORD_SPECIAL_RE.search(v):
            raise ValueError(
                "Password must contain at least one special character (e.g. ! @ # $ % ...)"
            )
        if len({c for c in v}) < 4:
            raise ValueError("Password must use at least 4 distinct characters")
        if v.lower() in COMMON_PASSWORDS:
            raise ValueError("This password is too common, please choose another")
        return v

    @model_validator(mode="after")
    def password_not_related_to_identity(self) -> "RegisterRequest":
        pwd_lower = self.password.lower()
        if self.username and self.username in pwd_lower:
            raise ValueError("Password must not contain your username")
        local_part = self.email.split("@", 1)[0] if self.email else ""
        if local_part and len(local_part) >= 3 and local_part.lower() in pwd_lower:
            raise ValueError("Password must not contain the local part of your email")
        return self


class LoginRequest(BaseModel):
    # `username` accepts either the username or the email address — the service
    # layer matches against both. We keep the field name for backwards
    # compatibility with existing clients.
    username: str = Field(..., min_length=1, max_length=254)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, v: str) -> str:
        if not v:
            raise ValueError("Username or email is required")
        # If the value looks like an email, normalise case to match how it was
        # stored at registration time.
        if "@" in v:
            return v.lower()
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required")
        return v


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


# --- Responses ---


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class UserLookupResponse(BaseModel):
    """Public-safe slice of a user record, used to resolve a recipient by
    email or username for a payment flow. Never includes balance, email or
    creation date."""

    id: int
    username: str
