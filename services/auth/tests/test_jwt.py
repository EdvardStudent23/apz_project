import pytest
from datetime import datetime, timezone

from src.services.jwt import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:

    def test_hash_is_not_plain(self):
        hashed = hash_password("MyPassword1")
        assert hashed != "MyPassword1"

    def test_verify_correct_password(self):
        hashed = hash_password("MyPassword1")
        assert verify_password("MyPassword1", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("MyPassword1")
        assert verify_password("WrongPass1", hashed) is False

    def test_same_password_different_hash(self):
        # bcrypt додає salt — два хеші одного пароля різні
        h1 = hash_password("MyPassword1")
        h2 = hash_password("MyPassword1")
        assert h1 != h2


class TestAccessToken:

    def test_create_and_decode(self):
        token, jti, expires_at = create_access_token(user_id=42, username="john")
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["username"] == "john"
        assert payload["type"] == "access"
        assert payload["jti"] == jti

    def test_expires_at_in_future(self):
        _, _, expires_at = create_access_token(user_id=1, username="john")
        assert expires_at > datetime.now(timezone.utc)

    def test_jti_is_unique(self):
        _, jti1, _ = create_access_token(1, "john")
        _, jti2, _ = create_access_token(1, "john")
        assert jti1 != jti2


class TestRefreshToken:

    def test_create_and_decode(self):
        token, jti, _ = create_refresh_token(user_id=42)
        payload = decode_token(token)

        assert payload["sub"] == "42"
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti

    def test_refresh_lives_longer_than_access(self):
        _, _, access_exp = create_access_token(1, "john")
        _, _, refresh_exp = create_refresh_token(1)
        assert refresh_exp > access_exp


class TestDecodeToken:

    def test_invalid_token_returns_none(self):
        result = decode_token("this.is.not.a.token")
        assert result is None

    def test_empty_string_returns_none(self):
        result = decode_token("")
        assert result is None

    def test_tampered_token_returns_none(self):
        token, _, _ = create_access_token(1, "john")
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None
