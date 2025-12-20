from copy import deepcopy
from collections import defaultdict
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
    async def ensure_record(
        self, uid: int, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[AccessLevel, bool]:
        defaults = defaults or {"access_level": 0}
        obj, created = await AccessLevel.get_or_create(
            uid=uid, chat_id=chat_id, defaults=defaults
        )
        return obj, created

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

        self._index_by_chat: Dict[int, Set[CacheKey]] = defaultdict(set)
        self._index_by_uid: Dict[int, Set[CacheKey]] = defaultdict(set)
        self._index_by_custom_name: Dict[Tuple[int, str], Set[CacheKey]] = defaultdict(set)

    def _index_add(self, key: CacheKey, row: CachedAccessLevelRow):
        uid, chat_id = key
        self._index_by_uid[uid].add(key)
        self._index_by_chat[chat_id].add(key)
        if row.custom_level_name:
            self._index_by_custom_name[(chat_id, row.custom_level_name)].add(key)

    def _index_remove(self, key: CacheKey, row: CachedAccessLevelRow):
        uid, chat_id = key
        self._index_by_uid.get(uid, set()).discard(key)
        self._index_by_chat.get(chat_id, set()).discard(key)
        if row.custom_level_name:
            self._index_by_custom_name.get((chat_id, row.custom_level_name), set()).discard(key)

    def _index_update_custom(self, key: CacheKey, old: Optional[str], new: Optional[str]):
        chat_id = key[1]
        if old:
            self._index_by_custom_name.get((chat_id, old), set()).discard(key)
        if new:
            self._index_by_custom_name[(chat_id, new)].add(key)

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()
            self._index_by_chat.clear()
            self._index_by_uid.clear()
            self._index_by_custom_name.clear()

            for row in await AccessLevel.all():
                key = _make_cache_key(row.uid, row.chat_id)
                cached = CachedAccessLevelRow.from_model(row)
                self._cache[key] = cached
                self._index_add(key, cached)
        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        initial_data = initial_data or {"access_level": 0}
        async with self._lock:
            if cache_key in self._cache:
                return False

        uid, chat_id = cache_key
        model, created = await self.repo.ensure_record(uid, chat_id, defaults=initial_data)
        cached = CachedAccessLevelRow.from_model(model)

        async with self._lock:
            self._cache[cache_key] = cached
            self._index_add(cache_key, cached)

        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedAccessLevelRow]:
        async with self._lock:
            row = self._cache.get(cache_key)
            return deepcopy(row) if row else None

    async def get_access_level(self, cache_key: CacheKey) -> int:
        async with self._lock:
            row = self._cache.get(cache_key)
            return row.access_level if row else 0

    async def edit(self, cache_key: CacheKey, **fields):
        await self._ensure_cached(cache_key, fields)
        async with self._lock:
            row = self._cache[cache_key]
            old_custom = row.custom_level_name
            for k, v in fields.items():
                setattr(row, k, v)
            if "custom_level_name" in fields and old_custom != row.custom_level_name:
                self._index_update_custom(cache_key, old_custom, row.custom_level_name)
            self._dirty.add(cache_key)

    async def remove(self, cache_key: CacheKey) -> Optional[CachedAccessLevelRow]:
        removed = None
        async with self._lock:
            if cache_key in self._cache:
                row = self._cache[cache_key]
                removed = deepcopy(row)
                self._dirty.discard(cache_key)
                self._index_remove(cache_key, row)
                del self._cache[cache_key]

        if removed:
            await self.repo.delete_record(*cache_key)
        return removed

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            payloads = {k: self._cache[k].access_level for k in dirty if k in self._cache}

        if not payloads:
            return

        items = list(payloads.items())
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            uids = list({k[0] for k, _ in batch})

            existing = await AccessLevel.filter(uid__in=uids)
            existing_map = {
                _make_cache_key(r.uid, r.chat_id): r for r in existing
            }

            to_update, to_create = [], []
            for key, level in batch:
                if key in existing_map:
                    row = existing_map[key]
                    if row.access_level != level:
                        row.access_level = level
                        to_update.append(row)
                else:
                    uid, chat_id = key
                    to_create.append(AccessLevel(uid=uid, chat_id=chat_id, access_level=level))

            if to_update:
                await AccessLevel.bulk_update(to_update, fields=["access_level"], batch_size=batch_size)
            if to_create:
                await AccessLevel.bulk_create(to_create, batch_size=batch_size)

        async with self._lock:
            for key, val in payloads.items():
                cur = self._cache.get(key)
                if cur is None or cur.access_level == val:
                    self._dirty.discard(key)

    async def get_all(
        self,
        chat_id: Optional[int] = None,
        uid: Optional[int] = None,
        *,
        predicate: Optional[Callable[[CachedAccessLevelRow], Any]] = None,
    ) -> List[CachedAccessLevelRow]:
        predicate = predicate or (lambda i: i.access_level > 0)

        async with self._lock:
            if chat_id is not None:
                keys_chat = set(self._index_by_chat.get(chat_id, ()))
            else:
                keys_chat = None

            if uid is not None:
                keys_uid = set(self._index_by_uid.get(uid, ()))
            else:
                keys_uid = None

            if keys_chat is not None and keys_uid is not None:
                keys = keys_chat & keys_uid
            elif keys_chat is not None:
                keys = keys_chat
            elif keys_uid is not None:
                keys = keys_uid
            else:
                keys = set(self._cache.keys())

            result: List[CachedAccessLevelRow] = []
            for key in keys:
                row = self._cache.get(key)
                if row and predicate(row):
                    result.append(deepcopy(row))

        return result


class AccessLevelManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = AccessLevelRepository()
        self.cache = AccessLevelCache(self.repo, self._cache)

        self.get_all = self.cache.get_all

    async def initialize(self):
        await self.cache.initialize()

    async def get_holders(self, chat_id: int, level_name: str) -> List[CachedAccessLevelRow]:
        return await self.get_all(chat_id=chat_id, predicate=lambda i: i.custom_level_name == level_name)

    async def get_access_level(self, uid: int, chat_id: int) -> int:
        return await self.cache.get_access_level(_make_cache_key(uid, chat_id))

    async def get(self, uid: int, chat_id: int) -> Optional[CachedAccessLevelRow]:
        return await self.cache.get(_make_cache_key(uid, chat_id))

    async def edit_access_level(
        self,
        uid: int,
        chat_id: int,
        access_level: int,
        custom_level_name: Optional[str] = None,
    ):
        if access_level == 0:
            return await self.delete(uid, chat_id)

        if isinstance(access_level, CachedAccessLevelRow):
            access_level = access_level.access_level
        elif not isinstance(access_level, int):
            raise Exception("Invalid access level type")

        await self.cache.edit(
            _make_cache_key(uid, chat_id),
            access_level=access_level,
            custom_level_name=custom_level_name,
        )

    async def edit_custom_level_name(self, chat_id: int, access_level: int, custom_level_name: str):
        rows = await self.get_all(
            chat_id=chat_id,
            predicate=lambda i: i.access_level == access_level and i.custom_level_name is not None,
        )
        for row in rows:
            await self.cache.edit(
                _make_cache_key(row.uid, chat_id), custom_level_name=custom_level_name
            )

    async def delete(self, uid: int, chat_id: int) -> Optional[CachedAccessLevelRow]:
        return await self.cache.remove(_make_cache_key(uid, chat_id))

    async def delete_row(self, row: CachedAccessLevelRow) -> Optional[CachedAccessLevelRow]:
        return await self.cache.remove(_make_cache_key(row.uid, row.chat_id))

    async def delete_rows(self, rows: Iterable[CachedAccessLevelRow]) -> List[CachedAccessLevelRow]:
        removed: List[CachedAccessLevelRow] = []
        for row in rows:
            r = await self.delete_row(row)
            if r is not None:
                removed.append(r)
        return removed
