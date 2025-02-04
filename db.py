from psycopg_pool import AsyncConnectionPool, ConnectionPool

from config.config import DATABASE_STR


_pool = None
_syncpool = None


async def pool():
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(DATABASE_STR, min_size=100, max_size=300, open=False)
        await _pool.open()
    return _pool


def syncpool() -> ConnectionPool:
    global _syncpool
    if _syncpool is None:
        _syncpool = ConnectionPool(DATABASE_STR, max_size=100, open=False)
        _syncpool.open()
    return _syncpool
