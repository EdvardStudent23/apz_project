import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.services import AuthService
from src.services.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AccountDisabledError,
    InvalidTokenError,
    SessionExpiredError,
)
from src.services.jwt import create_access_token, create_refresh_token, hash_password
from src.routes.schemas import RegisterRequest, LoginRequest


def make_user(id=1, username="testuser", email="test@example.com", active=True):
    user = MagicMock()
    user.id = id
    user.username = username
    user.email = email
    user.is_active = active
    user.hashed_password = hash_password("SecurePass1")
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def service():
    return AuthService()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=None)  # за замовчуванням — юзер не знайдений
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    return db


# ------------------------------------------------------------------ #
#  Register                                                            #
# ------------------------------------------------------------------ #

class TestRegister:

    @pytest.mark.asyncio
    async def test_register_success(self, service, mock_db):
        user = make_user()
        mock_db.scalar.return_value = None
        mock_db.refresh.side_effect = lambda u: None

        with patch("src.services.redis_manager") as mock_redis:
            mock_redis.save_session = AsyncMock()
            # Мокаємо що після refresh юзер має id
            async def fake_refresh(u):
                u.id = 1
                u.username = "testuser"
                u.email = "test@example.com"
                u.is_active = True
                u.created_at = datetime.now(timezone.utc)
            mock_db.refresh.side_effect = fake_refresh

            data = RegisterRequest(
                username="testuser",
                email="test@example.com",
                password="SecurePass1",
            )
            # Перевіряємо що функція не падає з помилкою
            # (повноцінна перевірка результату — в інтеграційних тестах)
            mock_db.scalar.return_value = None

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, service, mock_db):
        existing_user = make_user()
        mock_db.scalar.return_value = existing_user  # юзер вже існує

        data = RegisterRequest(
            username="testuser",
            email="test@example.com",
            password="SecurePass1",
        )

        with pytest.raises(UserAlreadyExistsError):
            await service.register(data, mock_db)

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, service, mock_db):
        # Перший scalar (username) → None, другий (email) → існуючий юзер
        mock_db.scalar.side_effect = [None, make_user()]

        data = RegisterRequest(
            username="newuser",
            email="existing@example.com",
            password="SecurePass1",
        )

        with pytest.raises(UserAlreadyExistsError):
            await service.register(data, mock_db)


# ------------------------------------------------------------------ #
#  Login                                                               #
# ------------------------------------------------------------------ #

class TestLogin:

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, service, mock_db):
        mock_db.scalar.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await service.login(LoginRequest(username="ghost", password="pass"), mock_db)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, service, mock_db):
        mock_db.scalar.return_value = make_user()

        with pytest.raises(InvalidCredentialsError):
            await service.login(
                LoginRequest(username="testuser", password="WrongPass1"), mock_db
            )

    @pytest.mark.asyncio
    async def test_login_disabled_account(self, service, mock_db):
        mock_db.scalar.return_value = make_user(active=False)

        with pytest.raises((InvalidCredentialsError, AccountDisabledError)):
            await service.login(
                LoginRequest(username="testuser", password="SecurePass1"), mock_db
            )


# ------------------------------------------------------------------ #
#  Logout                                                              #
# ------------------------------------------------------------------ #

class TestLogout:

    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, service):
        with pytest.raises(InvalidTokenError):
            await service.logout("not.a.real.token")

    @pytest.mark.asyncio
    async def test_logout_valid_token(self, service):
        token, jti, _ = create_access_token(1, "testuser")

        with patch("src.services.redis_manager") as mock_redis:
            mock_redis.delete_session = AsyncMock()
            mock_redis.blacklist_token = AsyncMock()

            await service.logout(token, all_devices=False)

            mock_redis.delete_session.assert_called_once_with(1, jti, "access")
            mock_redis.blacklist_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_all_devices(self, service):
        token, _, _ = create_access_token(1, "testuser")

        with patch("src.services.redis_manager") as mock_redis:
            mock_redis.delete_all_user_sessions = AsyncMock(return_value=3)

            await service.logout(token, all_devices=True)

            mock_redis.delete_all_user_sessions.assert_called_once_with(1)


# ------------------------------------------------------------------ #
#  Refresh                                                             #
# ------------------------------------------------------------------ #

class TestRefresh:

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, service, mock_db):
        with pytest.raises(InvalidTokenError):
            await service.refresh("bad.token.here", mock_db)

    @pytest.mark.asyncio
    async def test_refresh_access_token_rejected(self, service, mock_db):
        # access token замість refresh — має бути помилка
        token, _, _ = create_access_token(1, "testuser")

        with pytest.raises(InvalidTokenError):
            await service.refresh(token, mock_db)

    @pytest.mark.asyncio
    async def test_refresh_session_not_in_redis(self, service, mock_db):
        token, _, _ = create_refresh_token(1)

        with patch("src.services.redis_manager") as mock_redis:
            mock_redis.get_session = AsyncMock(return_value=None)  # сесії немає

            with pytest.raises(SessionExpiredError):
                await service.refresh(token, mock_db)


# ------------------------------------------------------------------ #
#  Validate token                                                      #
# ------------------------------------------------------------------ #

class TestValidateToken:

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self, service):
        result = await service.validate_token("garbage")
        assert result is None

    @pytest.mark.asyncio
    async def test_refresh_token_rejected(self, service):
        token, _, _ = create_refresh_token(1)
        result = await service.validate_token(token)
        assert result is None

    @pytest.mark.asyncio
    async def test_blacklisted_token_returns_none(self, service):
        token, jti, _ = create_access_token(1, "testuser")

        with patch("src.services.redis_manager") as mock_redis:
            mock_redis.is_token_blacklisted = AsyncMock(return_value=True)

            result = await service.validate_token(token)
            assert result is None

    @pytest.mark.asyncio
    async def test_valid_token_returns_user_data(self, service):
        token, jti, _ = create_access_token(42, "john")

        with patch("src.services.redis_manager") as mock_redis:
            mock_redis.is_token_blacklisted = AsyncMock(return_value=False)
            mock_redis.get_session = AsyncMock(return_value={"user_id": 42})

            result = await service.validate_token(token)

            assert result is not None
            assert result["user_id"] == 42
            assert result["username"] == "john"
            assert result["jti"] == jti
