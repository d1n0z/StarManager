import asyncpg
from tortoise.backends.asyncpg.client import AsyncpgDBClient
from StarManager.core.db import pool


class DBClient(AsyncpgDBClient):
    async def create_connection(self, with_db: bool) -> None:
        self._pool = await self.create_pool()
        self._connection = None

    async def create_pool(self, **kwargs) -> asyncpg.Pool:
        return await pool()
    
    async def _close(self) -> None:
        pass
    
    async def close(self) -> None:
        pass
