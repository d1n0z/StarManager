from copy import deepcopy
from typing import Set, TypeAlias

from StarManager.core.managers.base import (
    BaseCacheManager,
    BaseManager,
)
from StarManager.core.tables import AllChats

CacheKey: TypeAlias = int
Cache: TypeAlias = Set[int]


class AllChatsCache(BaseCacheManager):
    def __init__(self, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Cache = set()

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            self._cache.update([row.chat_id for row in await AllChats.all()])

        await super().initialize()

    async def _ensure_cached(self, cache_key: CacheKey) -> bool:
        async with self._lock:
            if cache_key in self._cache:
                return False
            self._cache.add(cache_key)
            self._dirty.add(cache_key)
        return True

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty = list(self._dirty)

        if not dirty:
            return

        for i in range(0, len(dirty), batch_size):
            to_create = [AllChats(chat_id=cid) for cid in dirty[i : i + batch_size]]
            if to_create:
                await AllChats.bulk_create(to_create, batch_size=batch_size)

        async with self._lock:
            self._dirty.difference_update(dirty)

    async def read_all(self) -> Set[int]:
        async with self._lock:
            return deepcopy(self._cache)

    async def exists(self, cache_key: CacheKey):
        async with self._lock:
            return cache_key in self._cache


class AllChatsManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = set()
        self.cache = AllChatsCache(self._cache)

        self.read_all = self.cache.read_all
        self.exists = self.cache.exists

    async def initialize(self):
        await self.cache.initialize()

    async def create_if_not_exists(self, cid):
        return await self.cache._ensure_cached(cid)
