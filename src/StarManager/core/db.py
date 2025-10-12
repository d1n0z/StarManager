from asyncpg import create_pool as create_asyncpool

from StarManager.core.config import DATABASE_STR


_pool = None
_smallpool = None


async def pool():
    global _pool
    if _pool is None:
        _pool = await create_asyncpool(
            DATABASE_STR, 
            min_size=20, 
            max_size=200,
            max_inactive_connection_lifetime=60,
            timeout=30, 
            command_timeout=60,
            max_queries=50000,
            max_cached_statement_lifetime=300
        )
    return _pool


async def smallpool():
    global _smallpool
    if _smallpool is None:
        _smallpool = await create_asyncpool(DATABASE_STR, min_size=1, max_size=20, max_inactive_connection_lifetime=30,
                                            timeout=30, command_timeout=60)
    return _smallpool
