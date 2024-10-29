from psycopg_pool import AsyncConnectionPool, ConnectionPool

from config.config import DATABASE, USER, PASSWORD, DATABASE_HOST, DATABASE_PORT

_pool = None
_syncpool = None


async def pool():
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(f'postgresql://{USER}:{PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE}',
                                    max_size=200, open=False)
        await _pool.open()
    return _pool


def syncpool() -> ConnectionPool:
    global _syncpool
    if _syncpool is None:
        _syncpool = ConnectionPool(f'postgresql://{USER}:{PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE}',
                                   open=False)
        _syncpool.open()
    return _syncpool
