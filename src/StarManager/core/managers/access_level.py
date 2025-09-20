from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, TypeAlias

from tortoise.expressions import Q as Query

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import AccessLevel

CacheKey: TypeAlias = Tuple[int, int]


@dataclass
class _CachedAccessLevel(BaseCachedModel):
    access_level: int


class AccessLevelRepository(BaseRepository):
    def __init__(self, items: List[AccessLevel]):
        super().__init__()
        self._items = items

    async def ensure_record(
        self, uid: int, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[AccessLevel, bool]:
        defaults = defaults or {"access_level": 0}
        obj, _created = await AccessLevel.get_or_create(
            uid=uid, chat_id=chat_id, defaults=defaults
        )
        async with self._lock:
            if obj not in self._items:
                self._items.append(obj)
        return obj, _created

    async def get_record(self, uid: int, chat_id: int) -> Optional[AccessLevel]:
        async with self._lock:
            return next(
                (i for i in self._items if i.uid == uid and i.chat_id == chat_id),
                None,
            )

    async def delete_record(self, uid: int, chat_id: int):
        async with self._lock:
            self._items = [
                i for i in self._items if not (i.uid == uid and i.chat_id == chat_id)
            ]
        await AccessLevel.filter(uid=uid, chat_id=chat_id).delete()


class AccessLevelCache(BaseCacheManager):
    def __init__(self, repo: AccessLevelRepository, items: List[AccessLevel]):
        super().__init__()
        self._cache: Dict[CacheKey, _CachedAccessLevel] = {}
        self._dirty: Set[CacheKey] = set()
        self.repo = repo
        self._items = items

    def make_cache_key(self, uid: int, chat_id: int) -> CacheKey:
        return (uid, chat_id)

    async def initialize(self):
        async with self._lock:
            for row in self._items:
                key = self.make_cache_key(row.uid, row.chat_id)
                self._cache[key] = _CachedAccessLevel.from_model(row)
        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ):
        initial_data = initial_data or {"access_level": 0}
        async with self._lock:
            if cache_key in self._cache:
                return

        uid, chat_id = cache_key
        model, created = await self.repo.ensure_record(
            uid, chat_id, defaults=initial_data
        )
        async with self._lock:
            self._cache[cache_key] = _CachedAccessLevel.from_model(model)
        return created

    async def get(self, cache_key: CacheKey) -> int:
        async with self._lock:
            obj = self._cache.get(cache_key)
            return obj.access_level if obj else 0

    async def edit(self, cache_key: CacheKey, access_level: int):
        created = await self._ensure_cached(cache_key, {"access_level": access_level})
        async with self._lock:
            if not created:
                self._cache[cache_key].access_level = access_level
            self._dirty.add(cache_key)

    async def remove(self, cache_key: CacheKey):
        async with self._lock:
            if cache_key in self._cache:
                self._dirty.discard(cache_key)
                del self._cache[cache_key]
        uid, chat_id = cache_key
        await self.repo.delete_record(uid, chat_id)

    async def sync(self):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            payloads = {
                (uid, chat_id): self._cache[(uid, chat_id)].access_level
                for uid, chat_id in dirty
                if (uid, chat_id) in self._cache
            }

        query = Query()
        for uid, chat_id in payloads.keys():
            query |= Query(uid=uid, chat_id=chat_id)
        existing = await AccessLevel.filter(query) if query else []
        existing = {(row.uid, row.chat_id): row for row in existing}

        to_update, to_create = [], []
        for (uid, chat_id), access_level in payloads.items():
            if (uid, chat_id) in existing:
                row = existing[(uid, chat_id)]
                row.access_level = access_level
                to_update.append(row)
            else:
                to_create.append(
                    AccessLevel(uid=uid, chat_id=chat_id, access_level=access_level)
                )

        if to_update:
            await AccessLevel.bulk_update(to_update, fields=["access_level"])
        if to_create:
            await AccessLevel.bulk_create(to_create)

        async with self._lock:
            self._dirty.difference_update(dirty)


class AccessLevelManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._items: List[AccessLevel] = []
        self.repo: AccessLevelRepository = AccessLevelRepository(self._items)
        self.cache: AccessLevelCache = AccessLevelCache(self.repo, self._items)

    async def initialize(self):
        rows = await AccessLevel.all()
        async with self._lock:
            self._items.extend(rows)
        await self.cache.initialize()

    def make_key(self, uid: int, chat_id: int) -> CacheKey:
        return self.cache.make_cache_key(uid, chat_id)

    async def get_access_level(self, uid: int, chat_id: int) -> int:
        return await self.cache.get(self.make_key(uid, chat_id))

    async def edit_access_level(self, uid: int, chat_id: int, access_level: int):
        if access_level == 0:
            return await self.delete(uid, chat_id)
        await self.cache.edit(self.make_key(uid, chat_id), access_level)

    async def delete(self, uid: int, chat_id: int):
        await self.cache.remove(self.make_key(uid, chat_id))

    async def sync(self):
        await self.cache.sync()
