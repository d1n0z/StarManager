from dataclasses import dataclass
from typing import Dict, Set, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
)
from StarManager.core.tables import Prefixes


@dataclass
class CachedPrefixesRow(BaseCachedModel):
    uid: int
    prefixes: Set[str]


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedPrefixesRow]


class PrefixesCache(BaseCacheManager):
    def __init__(self, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await Prefixes.all():
                key = row.uid
                if key not in self._cache:
                    self._cache[key] = CachedPrefixesRow(
                        uid=row.uid, prefixes=set()
                    )
                self._cache[key].prefixes.add(row.prefix)

        await super().initialize()

    async def sync(self, batch_size: int = 200):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            payloads = {k: self._cache[k].prefixes for k in dirty if k in self._cache}

        if not payloads:
            return

        items = list(payloads.items())
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]

            existing_rows = await Prefixes.filter(uid__in=[key for key, _ in batch])
            existing_map: dict = {}
            for r in existing_rows:
                key = r.uid
                existing_map.setdefault(key, set()).add(r.prefix)

            to_create = []
            to_delete_by_key = {}

            for key, cached_prefixes in batch:
                uid = key
                db_prefixes = existing_map.get(key, set())

                create_prefixes = cached_prefixes - db_prefixes
                for f in create_prefixes:
                    to_create.append(Prefixes(uid=uid, prefix=f))

                delete_prefixes = db_prefixes - cached_prefixes
                if delete_prefixes:
                    to_delete_by_key[key] = delete_prefixes

            if to_create:
                await Prefixes.bulk_create(
                    to_create, ignore_conflicts=True, batch_size=batch_size
                )

            for uid, del_prefixes in to_delete_by_key.items():
                await Prefixes.filter(uid=uid, prefix__in=list(del_prefixes)).delete()

        async with self._lock:
            self._dirty.difference_update(dirty)

    async def new_prefix(self, key: CacheKey, prefix: str):
        uid = key
        async with self._lock:
            if key not in self._cache:
                self._cache[key] = CachedPrefixesRow(uid=uid, prefixes=set())
            elif prefix in self._cache[key].prefixes:
                return False
            self._cache[key].prefixes.add(prefix)
            self._dirty.add(key)
        return True

    async def del_prefix(self, key: CacheKey, prefix: str):
        async with self._lock:
            if key not in self._cache or prefix not in self._cache[key].prefixes:
                return False
            self._cache[key].prefixes.remove(prefix)
            self._dirty.add(key)
        return True

    async def prefix_exists(self, key: CacheKey, prefix: str):
        async with self._lock:
            return key in self._cache and prefix in self._cache[key].prefixes

    async def get_all_prefixes(self, key: CacheKey) -> Set[str]:
        async with self._lock:
            if key in self._cache:
                return self._cache[key].prefixes
            return set()

    async def del_all_prefixes(self, key: CacheKey):
        async with self._lock:
            if key not in self._cache:
                return False
            self._cache[key].prefixes.clear()
            self._dirty.add(key)
        return True


class PrefixesManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.cache = PrefixesCache(self._cache)

    async def prefix_exists(self, uid: int, prefix: str):
        return await self.cache.prefix_exists(uid, prefix)

    async def new_prefix(self, uid: int, prefix: str):
        return await self.cache.new_prefix(uid, prefix)

    async def del_prefix(self, uid: int, prefix: str):
        return await self.cache.del_prefix(uid, prefix)

    async def del_all_prefixes(self, uid: int):
        return await self.cache.del_all_prefixes(uid)

    async def get_all(self, uid: int) -> Set[str]:
        return await self.cache.get_all_prefixes(uid)
