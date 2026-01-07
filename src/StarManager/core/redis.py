from redis import asyncio as aioredis

from StarManager.core.config import settings


class RedisManager:
    def __init__(self):
        self._redis = None

    async def init(self):
        self._redis = await aioredis.Redis.from_url(
            "redis://localhost:6379",
            password=settings.database.password,
            encoding="utf-8",
            decode_responses=True,
        )

    @property
    def redis(self):
        if self._redis is None:
            raise RuntimeError(
                "Redis client is not initialized. You have to execute RedisManager.init() first"
            )
        return self._redis
