from dataclasses import dataclass
from typing import Dict, Set, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
)
from StarManager.core.tables import FiltersExceptions

from .filtering import normalize_text


@dataclass
class CachedFiltersExceptionsRow(BaseCachedModel):
    chat_id: int
    filters: Set[str]


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedFiltersExceptionsRow]


class FiltersExceptionsCache(BaseCacheManager):
    def __init__(self, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await FiltersExceptions.all():
                key = row.chat_id
                if key not in self._cache:
                    self._cache[key] = CachedFiltersExceptionsRow(
                        chat_id=row.chat_id, filters=set()
                    )
                self._cache[key].filters.add(row.filter_)

        await super().initialize()

    async def sync(self, batch_size: int = 200):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            payloads = {k: self._cache[k].filters for k in dirty if k in self._cache}

        if not payloads:
            return

        items = list(payloads.items())
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]

            existing_rows = await FiltersExceptions.filter(
                chat_id__in=[key for key, _ in batch]
            )
            existing_map: dict = {}
            for r in existing_rows:
                key = r.chat_id
                existing_map.setdefault(key, set()).add(r.filter_)

            to_create = []
            to_delete_by_key = {}

            for key, cached_filters in batch:
                chat_id = key
                db_filters = existing_map.get(key, set())

                create_filters = cached_filters - db_filters
                for f in create_filters:
                    to_create.append(FiltersExceptions(chat_id=chat_id, filter_=f))

                delete_filters = db_filters - cached_filters
                if delete_filters:
                    to_delete_by_key[key] = delete_filters

            if to_create:
                await FiltersExceptions.bulk_create(
                    to_create, ignore_conflicts=True, batch_size=batch_size
                )

            for chat_id, del_filters in to_delete_by_key.items():
                await FiltersExceptions.filter(
                    chat_id=chat_id, filter___in=list(del_filters)
                ).delete()

        async with self._lock:
            self._dirty.difference_update(dirty)

    async def new_filter(self, key: CacheKey, filter_: str):
        chat_id = key
        async with self._lock:
            if key not in self._cache:
                self._cache[key] = CachedFiltersExceptionsRow(
                    chat_id=chat_id, filters=set()
                )
            elif filter_ in self._cache[key].filters:
                return False
            self._cache[key].filters.add(filter_)
            self._dirty.add(key)
        return True

    async def del_filter(self, key: CacheKey, filter_: str):
        async with self._lock:
            if key not in self._cache or filter_ not in self._cache[key].filters:
                return False
            self._cache[key].filters.remove(filter_)
            self._dirty.add(key)
        return True

    async def filter_exists(self, key: CacheKey, filter_: str):
        async with self._lock:
            return key in self._cache and any(
                (
                    normalize_text(filter_) == normalize_text(i)
                    for i in self._cache[key].filters
                )
            )

    async def get_all_filters(self, key: CacheKey) -> Set[str]:
        async with self._lock:
            if key in self._cache:
                return self._cache[key].filters
            return set()


class FiltersExceptionsManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.cache = FiltersExceptionsCache(self._cache)

    async def filter_exists(self, chat_id: int, filter_: str):
        return await self.cache.filter_exists(chat_id, filter_)

    async def new_filter(self, chat_id: int, filter_: str):
        return await self.cache.new_filter(chat_id, filter_)

    async def del_filter(self, chat_id: int, filter_: str):
        return await self.cache.del_filter(chat_id, filter_)

    async def get_all(self, chat_id: int):
        return await self.cache.get_all_filters(chat_id)
