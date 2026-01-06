from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import LvlBanned


@dataclass
class CachedLvlBannedRow(BaseCachedModel):
    uid: int


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedLvlBannedRow]


def _make_cache_key(uid: int) -> CacheKey:
    return uid


class LvlBannedRepository(BaseRepository):
    async def ensure_record(self, uid: int):
        return await LvlBanned.get_or_create(uid=uid)

    async def delete_record(self, uid: int):
        await LvlBanned.filter(uid=uid).delete()

    async def delete_multiple(self, uids: Iterable[int]):
        uids = list(uids)
        if not uids:
            return
        chunk_size = 1000
        for i in range(0, len(uids), chunk_size):
            await LvlBanned.filter(uid__in=uids[i : i + chunk_size]).delete()

    async def get_existing_uids(self, uids: Iterable[int]) -> Set[int]:
        uids = list(uids)
        if not uids:
            return set()
        existing = await LvlBanned.filter(uid__in=uids).all()
        return {r.uid for r in existing}


class LvlBannedCache(BaseCacheManager):
    def __init__(self, repo: LvlBannedRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self.repo = repo
        self._to_add: Set[CacheKey] = set()
        self._to_remove: Set[CacheKey] = set()

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._to_add.clear()
            self._to_remove.clear()
            for row in await LvlBanned.all():
                key = _make_cache_key(row.uid)
                self._cache[key] = CachedLvlBannedRow(uid=row.uid)
        await super().initialize()

    async def exists(self, uid: int) -> bool:
        async with self._lock:
            return _make_cache_key(uid) in self._cache

    async def get(self, uid: int) -> Optional[CachedLvlBannedRow]:
        async with self._lock:
            row = self._cache.get(_make_cache_key(uid))
            return deepcopy(row) if row else None

    async def add(self, uid: int) -> bool:
        key = _make_cache_key(uid)
        async with self._lock:
            if key in self._cache:
                return False
            self._cache[key] = CachedLvlBannedRow(uid=uid)
            if key in self._to_remove:
                self._to_remove.discard(key)
            else:
                self._to_add.add(key)
        return True

    async def remove(self, uid: int) -> bool:
        key = _make_cache_key(uid)
        async with self._lock:
            if key not in self._cache:
                return False
            del self._cache[key]
            if key in self._to_add:
                self._to_add.discard(key)
            else:
                self._to_remove.add(key)
        return True

    async def get_all_uids(self) -> List[int]:
        async with self._lock:
            return list(self._cache.keys())

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            to_add = set(self._to_add)
            to_remove = set(self._to_remove)

        if to_remove:
            keys = list(to_remove)
            for i in range(0, len(keys), batch_size):
                chunk = keys[i : i + batch_size]
                try:
                    await self.repo.delete_multiple(chunk)
                except Exception:
                    pass

        if to_add:
            keys = list(to_add)
            existing = await self.repo.get_existing_uids(keys)
            to_create = [k for k in keys if k not in existing]
            items = [LvlBanned(uid=uid) for uid in to_create]
            for i in range(0, len(items), batch_size):
                chunk = items[i : i + batch_size]
                try:
                    if chunk:
                        await LvlBanned.bulk_create(chunk, batch_size=batch_size)
                except Exception:
                    pass

        async with self._lock:
            for k in to_add:
                self._to_add.discard(k)
            for k in to_remove:
                self._to_remove.discard(k)


class LvlBannedManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = LvlBannedRepository()
        self.cache = LvlBannedCache(self.repo, self._cache)

    async def initialize(self):
        await self.cache.initialize()

    async def exists(self, uid: int) -> bool:
        return await self.cache.exists(uid)

    async def add(self, uid: int) -> bool:
        return await self.cache.add(uid)

    async def remove(self, uid: int) -> bool:
        return await self.cache.remove(uid)

    async def get_all_uids(self) -> List[int]:
        return await self.cache.get_all_uids()
