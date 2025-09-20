from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, Tuple, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import AccessLevel


@dataclass
class _CachedAccessLevel(BaseCachedModel):
    access_level: int


CacheKey: TypeAlias = Tuple[int, int]
Cache: TypeAlias = Dict[CacheKey, _CachedAccessLevel]


def _make_cache_key(uid: int, chat_id: int) -> CacheKey:
    return (uid, chat_id)


class AccessLevelRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def ensure_record(
        self, uid: int, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[AccessLevel, bool]:
        defaults = defaults or {"access_level": 0}
        obj, _created = await AccessLevel.get_or_create(
            uid=uid, chat_id=chat_id, defaults=defaults
        )
        return obj, _created

    async def get_record(self, uid: int, chat_id: int) -> Optional[AccessLevel]:
        return await AccessLevel.filter(uid=uid, chat_id=chat_id).first()

    async def delete_record(self, uid: int, chat_id: int):
        await AccessLevel.filter(uid=uid, chat_id=chat_id).delete()


class AccessLevelCache(BaseCacheManager):
    def __init__(self, repo: AccessLevelRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        async with self._lock:
            for row in await AccessLevel.all():
                key = _make_cache_key(row.uid, row.chat_id)
                self._cache[key] = _CachedAccessLevel.from_model(row)
        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ):
        initial_data = initial_data or {"access_level": 0}
        async with self._lock:
            if cache_key in self._cache:
                return False

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

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty_snapshot = set(self._dirty)
            payloads = {
                key: self._cache[key].access_level
                for key in dirty_snapshot
                if key in self._cache
            }

        if not payloads:
            return

        items = list(payloads.items())
        try:
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                uids = list({key[0] for key, _ in batch})

                existing_rows = await AccessLevel.filter(uid__in=uids)
                keys_set = {k for k, _ in batch}
                existing_map = {
                    _make_cache_key(row.uid, row.chat_id): row
                    for row in existing_rows
                    if _make_cache_key(row.uid, row.chat_id) in keys_set
                }

                to_update, to_create = [], []
                for key, access_level in batch:
                    if key in existing_map:
                        row = existing_map[key]
                        if row.access_level != access_level:
                            row.access_level = access_level
                            to_update.append(row)
                    else:
                        uid, chat_id = key
                        to_create.append(
                            AccessLevel(
                                uid=uid, chat_id=chat_id, access_level=access_level
                            )
                        )

                if to_update:
                    await AccessLevel.bulk_update(to_update, fields=["access_level"], batch_size=batch_size)
                if to_create:
                    await AccessLevel.bulk_create(to_create, batch_size=batch_size)
        except Exception:
            from loguru import logger

            logger.exception("AccessLevel sync failed")
            return

        async with self._lock:
            for key, old_val in payloads.items():
                cur = self._cache.get(key)
                if cur is None or cur.access_level == old_val:
                    self._dirty.discard(key)


class AccessLevelManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo: AccessLevelRepository = AccessLevelRepository()
        self.cache: AccessLevelCache = AccessLevelCache(self.repo, self._cache)

    async def initialize(self):
        await self.cache.initialize()

    async def get_access_level(self, uid: int, chat_id: int) -> int:
        return await self.cache.get(_make_cache_key(uid, chat_id))

    async def edit_access_level(self, uid: int, chat_id: int, access_level: int):
        if access_level == 0:
            return await self.delete(uid, chat_id)
        await self.cache.edit(_make_cache_key(uid, chat_id), access_level)

    async def delete(self, uid: int, chat_id: int):
        await self.cache.remove(_make_cache_key(uid, chat_id))

    async def sync(self):
        await self.cache.sync()
