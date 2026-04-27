import pytest
from pydantic import ValidationError

from src.routes.schemas import RegisterRequest, LoginRequest


class TestRegisterRequest:

    def test_valid_data(self):
        req = RegisterRequest(
            username="john_doe",
            email="john@example.com",
            password="SecurePass1",
        )
        assert req.username == "john_doe"

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="ab", email="a@b.com", password="SecurePass1")

    def test_username_invalid_chars(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="john doe", email="a@b.com", password="SecurePass1")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="john", email="not-an-email", password="SecurePass1")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="john", email="a@b.com", password="Pass1")

    def test_password_no_uppercase(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="john", email="a@b.com", password="password1")

    def test_password_no_digit(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="john", email="a@b.com", password="PasswordNoDigit")


class TestLoginRequest:

    def test_valid_login(self):
        req = LoginRequest(username="john", password="pass")
        assert req.username == "john"

    def test_login_with_email(self):
        req = LoginRequest(username="john@example.com", password="pass")
        assert req.username == "john@example.com"
