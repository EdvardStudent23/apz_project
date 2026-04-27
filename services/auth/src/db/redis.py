import json
from typing import Optional

import redis.asyncio as aioredis

from src.settings import settings


class RedisSessionManager:
    """
    Зберігає JWT сесії у Redis.
    Завдяки цьому два інстанси auth-service бачать одні й ті самі сесії —
    якщо один впаде, користувач залишається залогіненим через другий.
    """

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self._client.ping()

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> aioredis.Redis:
        if not self._client:
            raise RuntimeError("Redis not connected")
        return self._client

    # --- Session ---

    async def save_session(
        self,
        user_id: int,
        jti: str,
        token_type: str,
        ttl_seconds: int,
        extra: dict = None,
    ) -> None:
        key = self._key(user_id, jti, token_type)
        payload = {"user_id": user_id, "jti": jti, "token_type": token_type}
        if extra:
            payload.update(extra)
        await self.client.setex(key, ttl_seconds, json.dumps(payload))

    async def get_session(
        self, user_id: int, jti: str, token_type: str
    ) -> Optional[dict]:
        data = await self.client.get(self._key(user_id, jti, token_type))
        return json.loads(data) if data else None

    async def delete_session(self, user_id: int, jti: str, token_type: str) -> None:
        await self.client.delete(self._key(user_id, jti, token_type))

    async def delete_all_user_sessions(self, user_id: int) -> int:
        keys = await self.client.keys(f"session:{user_id}:*")
        return await self.client.delete(*keys) if keys else 0

    # --- Blacklist ---

    async def blacklist_token(self, jti: str, ttl_seconds: int) -> None:
        await self.client.setex(f"blacklist:{jti}", ttl_seconds, "1")

    async def is_token_blacklisted(self, jti: str) -> bool:
        return await self.client.exists(f"blacklist:{jti}") == 1

    @staticmethod
    def _key(user_id: int, jti: str, token_type: str) -> str:
        return f"session:{user_id}:{token_type}:{jti}"


redis_manager = RedisSessionManager()
