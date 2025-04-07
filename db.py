from asyncpg import create_pool as create_asyncpool
from psycopg_pool import ConnectionPool

from config.config import DATABASE_STR


async def init_connection(conn):  # just testin'
    await conn.execute("SET idle_in_transaction_session_timeout = '15s'")

_pool = None
_syncpool = None


async def pool():
    global _pool
    if _pool is None:
        _pool = await create_asyncpool(DATABASE_STR, min_size=5, max_size=80, max_inactive_connection_lifetime=30,
                                       timeout=30, command_timeout=60, init=init_connection)
    return _pool


async def smallpool():
    global _pool
    if _pool is None:
        _pool = await create_asyncpool(DATABASE_STR, min_size=1, max_inactive_connection_lifetime=30)
    return _pool


def syncpool() -> ConnectionPool:
    global _syncpool
    if _syncpool is None:
        _syncpool = ConnectionPool(DATABASE_STR, min_size=1, max_size=10, open=False)
        _syncpool.open()
    return _syncpool
