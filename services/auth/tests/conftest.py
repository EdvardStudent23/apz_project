import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from src.api import app
from src.db.models import User


# ------------------------------------------------------------------ #
#  Мок Redis — щоб тести не потребували реального Redis              #
# ------------------------------------------------------------------ #

@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Підміняє redis_manager на мок для всіх тестів."""
    store = {}
    blacklist = set()

    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()

    async def save_session(user_id, jti, token_type, ttl_seconds, extra=None):
        key = f"{user_id}:{token_type}:{jti}"
        store[key] = {"user_id": user_id, "jti": jti, "token_type": token_type}

    async def get_session(user_id, jti, token_type):
        return store.get(f"{user_id}:{token_type}:{jti}")

    async def delete_session(user_id, jti, token_type):
        store.pop(f"{user_id}:{token_type}:{jti}", None)

    async def delete_all_user_sessions(user_id):
        keys = [k for k in store if k.startswith(f"{user_id}:")]
        for k in keys:
            del store[k]
        return len(keys)

    async def blacklist_token(jti, ttl):
        blacklist.add(jti)

    async def is_token_blacklisted(jti):
        return jti in blacklist

    mock.save_session = save_session
    mock.get_session = get_session
    mock.delete_session = delete_session
    mock.delete_all_user_sessions = delete_all_user_sessions
    mock.blacklist_token = blacklist_token
    mock.is_token_blacklisted = is_token_blacklisted

    # Мок для ping (healthcheck)
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock.client = mock_client

    monkeypatch.setattr("src.db.redis.redis_manager", mock)
    monkeypatch.setattr("src.services.redis_manager", mock)
    monkeypatch.setattr("src.routes.dependencies.auth_service.__class__", type)

    return mock, store, blacklist


# ------------------------------------------------------------------ #
#  Мок DB — щоб тести не потребували PostgreSQL                      #
# ------------------------------------------------------------------ #

@pytest.fixture
def mock_user():
    """Готовий об'єкт User для тестів."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    from datetime import datetime, timezone
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest_asyncio.fixture
async def client():
    """HTTP клієнт для тестування ендпоінтів."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
