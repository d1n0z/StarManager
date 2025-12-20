from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import AccessLevel


@dataclass
class CachedAccessLevelRow(BaseCachedModel):
    uid: int
    chat_id: int
    access_level: int
    custom_level_name: Optional[str] = None


CacheKey: TypeAlias = Tuple[int, int]
Cache: TypeAlias = Dict[CacheKey, CachedAccessLevelRow]


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
                self._cache[key] = CachedAccessLevelRow.from_model(row)
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
            self._cache[cache_key] = CachedAccessLevelRow.from_model(model)
        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedAccessLevelRow]:
        async with self._lock:
            return self._cache.get(cache_key)

    async def get_access_level(self, cache_key: CacheKey) -> int:
        async with self._lock:
            obj = self._cache.get(cache_key)
            return obj.access_level if obj else 0

    async def edit(self, cache_key: CacheKey, **fields):
        created = await self._ensure_cached(cache_key, fields)
        async with self._lock:
            if not created:
                for k, v in fields.items():
                    setattr(self._cache[cache_key], k, v)
            self._dirty.add(cache_key)

    async def remove(self, cache_key: CacheKey):
        removed_item = None
        async with self._lock:
            if cache_key in self._cache:
                removed_item = deepcopy(self._cache[cache_key])
                self._dirty.discard(cache_key)
                del self._cache[cache_key]

        if removed_item is not None:
            await self.repo.delete_record(*cache_key)

        return removed_item

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
                    await AccessLevel.bulk_update(
                        to_update, fields=["access_level"], batch_size=batch_size
                    )
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

    async def get_all(
        self,
        chat_id: Optional[int] = None,
        uid: Optional[int] = None,
        *,
        predicate: Optional[Callable[[CachedAccessLevelRow], Any]] = None,
    ) -> List[CachedAccessLevelRow]:
        predicate = predicate or (lambda i: i.access_level > 0)

        def predicate_chat_id(i: CachedAccessLevelRow):
            if chat_id is None:
                return True
            return i.chat_id == chat_id

        def predicate_uid(i: CachedAccessLevelRow):
            if uid is None:
                return i.uid > 0
            return i.uid == uid

        def pred(i: CachedAccessLevelRow):
            return predicate(i) and predicate_chat_id(i) and predicate_uid(i)

        async with self._lock:
            snapshot = list(self._cache.values())
        return [deepcopy(i) for i in snapshot if pred(i)]


class AccessLevelManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo: AccessLevelRepository = AccessLevelRepository()
        self.cache: AccessLevelCache = AccessLevelCache(self.repo, self._cache)

        self.get_all = self.cache.get_all

    async def initialize(self):
        await self.cache.initialize()

    async def get_holders(self, chat_id: int, level_name: str) -> List[CachedAccessLevelRow]:
        return await self.get_all(chat_id, predicate=lambda i: i.custom_level_name == level_name)

    async def get_access_level(self, uid: int, chat_id: int) -> int:
        return await self.cache.get_access_level(_make_cache_key(uid, chat_id))

    async def get(self, uid: int, chat_id: int) -> Optional[CachedAccessLevelRow]:
        return await self.cache.get(_make_cache_key(uid, chat_id))

    async def edit_access_level(
        self, uid: int, chat_id: int, access_level: int | CachedAccessLevelRow, custom_level_name: Optional[str] = None
    ) -> Optional[CachedAccessLevelRow]:
        if access_level == 0:
            return await self.delete(uid, chat_id)
        if isinstance(access_level, CachedAccessLevelRow):
            access_level = access_level.access_level
        elif not isinstance(access_level, int):
            raise Exception("Invalid access level type")
        await self.cache.edit(_make_cache_key(uid, chat_id), access_level=access_level, custom_level_name=custom_level_name)

    async def edit_custom_level_name(
        self, chat_id: int, access_level: int, custom_level_name: str
    ):
        to_edit = await self.get_all(
            chat_id=chat_id, predicate=lambda i: (i.access_level == access_level and i.custom_level_name is not None)
        )
        for i in to_edit:
            await self.cache.edit(
                _make_cache_key(i.uid, chat_id), custom_level_name=custom_level_name
            )

    async def delete(self, uid: int, chat_id: int) -> Optional[CachedAccessLevelRow]:
        return await self.cache.remove(_make_cache_key(uid, chat_id))

    async def delete_row(
        self, row: CachedAccessLevelRow
    ) -> Optional[CachedAccessLevelRow]:
        return await self.cache.remove(_make_cache_key(row.uid, row.chat_id))

    async def delete_rows(
        self, rows: Iterable[CachedAccessLevelRow]
    ) -> List[CachedAccessLevelRow]:
        return [row for row in rows if await self.delete_row(row) is not None]
