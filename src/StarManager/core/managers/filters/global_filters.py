from dataclasses import dataclass
from typing import Dict, Optional, Set, TypeAlias

import ahocorasick

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
)
from StarManager.core.managers.filters import filtering
from StarManager.core.tables import GlobalFilters

from .filtering import Matcher, normalize_text


@dataclass
class CachedGlobalFiltersRow(BaseCachedModel):
    owner_id: int
    filters: Set[str]


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedGlobalFiltersRow]


class GlobalFiltersCache(BaseCacheManager):
    def __init__(self, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self._matchers: Dict[CacheKey, Matcher] = {}

    def _build_matcher_for_key(self, key: CacheKey):
        cached = self._cache.get(key)
        if not cached or not cached.filters:
            self._matchers.pop(key, None)
            return

        norm_filters = {normalize_text(f) for f in cached.filters if f and f.strip()}
        norm_filters = {f for f in norm_filters if f}
        if not norm_filters:
            self._matchers.pop(key, None)
            return

        matcher = Matcher(normalized_filters=norm_filters)

        A = ahocorasick.Automaton()
        for i, pat in enumerate(sorted(norm_filters, key=len, reverse=True)):
            A.add_word(pat, pat)
        A.make_automaton()
        matcher.automaton = A
        matcher.regex_list = None

        self._matchers[key] = matcher

    def _rebuild_matcher_if_needed(self, key: CacheKey):
        return self._build_matcher_for_key(key)

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await GlobalFilters.all():
                key = row.owner_id
                if key not in self._cache:
                    self._cache[key] = CachedGlobalFiltersRow(
                        owner_id=row.owner_id, filters=set()
                    )
                self._cache[key].filters.add(row.filter_)

            for key in list(self._cache.keys()):
                self._build_matcher_for_key(key)

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

            existing_rows = await GlobalFilters.filter(
                owner_id__in=[key for key, _ in batch]
            )
            existing_map: dict = {}
            for r in existing_rows:
                key = r.owner_id
                existing_map.setdefault(key, set()).add(r.filter_)

            to_create = []
            to_delete_by_key = {}

            for key, cached_filters in batch:
                owner_id = key
                db_filters = existing_map.get(key, set())

                create_filters = cached_filters - db_filters
                for f in create_filters:
                    to_create.append(GlobalFilters(owner_id=owner_id, filter_=f))

                delete_filters = db_filters - cached_filters
                if delete_filters:
                    to_delete_by_key[key] = delete_filters

            if to_create:
                await GlobalFilters.bulk_create(
                    to_create, ignore_conflicts=True, batch_size=batch_size
                )

            for owner_id, del_filters in to_delete_by_key.items():
                await GlobalFilters.filter(
                    owner_id=owner_id, filter___in=list(del_filters)
                ).delete()

        async with self._lock:
            self._dirty.difference_update(dirty)

    async def new_filter(self, key: CacheKey, filter_: str):
        owner_id = key
        async with self._lock:
            if key not in self._cache:
                self._cache[key] = CachedGlobalFiltersRow(
                    owner_id=owner_id, filters=set()
                )
            elif filter_ in self._cache[key].filters:
                return False
            self._cache[key].filters.add(filter_)
            self._dirty.add(key)
            self._rebuild_matcher_if_needed(key)
        return True

    async def del_filter(self, key: CacheKey, filter_: str):
        async with self._lock:
            if key not in self._cache or filter_ not in self._cache[key].filters:
                return False
            self._cache[key].filters.remove(filter_)
            self._dirty.add(key)
            self._rebuild_matcher_if_needed(key)
        return True

    def matches(self, key: CacheKey, text: str) -> Optional[str]:
        return filtering.matches(self._matchers.get(key), text)

    async def filter_exists(self, key: CacheKey, filter_: str):
        async with self._lock:
            return key in self._cache and filter_ in self._cache[key].filters

    async def get_all_filters(self, key: CacheKey) -> Set[str]:
        async with self._lock:
            if key in self._cache:
                return self._cache[key].filters
            return set()

    async def del_all_filters(self, key: CacheKey):
        async with self._lock:
            if key not in self._cache:
                return False
            self._cache[key].filters.clear()
            self._dirty.add(key)
            self._rebuild_matcher_if_needed(key)
        return True


class GlobalFiltersManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.cache = GlobalFiltersCache(self._cache)

    async def filter_exists(self, owner_id: int, filter_: str):
        return await self.cache.filter_exists(owner_id, filter_)

    async def new_filter(self, owner_id: int, filter_: str):
        return await self.cache.new_filter(owner_id, filter_)

    async def del_filter(self, owner_id: int, filter_: str):
        return await self.cache.del_filter(owner_id, filter_)

    async def del_all_filters(self, owner_id: int):
        return await self.cache.del_all_filters(owner_id)

    def matches(self, owner_id: int, message: str):
        return self.cache.matches(owner_id, message)

    async def get_all(self, owner_id: int):
        return await self.cache.get_all_filters(owner_id)
