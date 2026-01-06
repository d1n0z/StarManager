from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, Tuple, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import ChatLimit


@dataclass
class CachedChatLimitRow(BaseCachedModel):
    chat_id: int
    time: int


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedChatLimitRow]


def _make_cache_key(chat_id: int) -> CacheKey:
    return chat_id


class ChatLimitRepository(BaseRepository):
    async def ensure_record(
        self, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[ChatLimit, bool]:
        obj, created = await ChatLimit.get_or_create(chat_id=chat_id, defaults=defaults)
        return obj, created

    async def delete_record(self, chat_id: int):
        await ChatLimit.filter(chat_id=chat_id).delete()


class ChatLimitCache(BaseCacheManager):
    def __init__(self, repo: ChatLimitRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await ChatLimit.all():
                key = _make_cache_key(row.chat_id)
                cached = CachedChatLimitRow.from_model(row)
                self._cache[key] = cached
        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        initial_data = initial_data or {"time": 0}
        async with self._lock:
            if cache_key in self._cache:
                return False

        chat_id = cache_key
        model, created = await self.repo.ensure_record(chat_id, defaults=initial_data)
        cached = CachedChatLimitRow.from_model(model)

        async with self._lock:
            self._cache[cache_key] = cached

        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedChatLimitRow]:
        async with self._lock:
            row = self._cache.get(cache_key)
            return deepcopy(row) if row else None

    async def edit(self, cache_key: CacheKey, **fields):
        created = await self._ensure_cached(cache_key, fields)
        async with self._lock:
            row = self._cache[cache_key]
            for k, v in fields.items():
                setattr(row, k, v)
            self._dirty.add(cache_key)
        return created

    async def remove(self, cache_key: CacheKey) -> Optional[CachedChatLimitRow]:
        removed = None
        async with self._lock:
            if cache_key in self._cache:
                row = self._cache[cache_key]
                removed = deepcopy(row)
                self._dirty.discard(cache_key)
                del self._cache[cache_key]

        if removed:
            await self.repo.delete_record(cache_key)
        return removed

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            payloads = {k: self._cache[k].time for k in dirty if k in self._cache}

        if not payloads:
            return

        items = list(payloads.items())
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            uids = list({k for k, _ in batch})

            existing = await ChatLimit.filter(uid__in=uids)
            existing_map = {_make_cache_key(r.chat_id): r for r in existing}

            to_update, to_create = [], []
            for key, time in batch:
                if key in existing_map:
                    row = existing_map[key]
                    if row.time != time:
                        row.time = time
                        to_update.append(row)
                else:
                    to_create.append(ChatLimit(chat_id=key, time=time))

            if to_update:
                await ChatLimit.bulk_update(
                    to_update, fields=["time"], batch_size=batch_size
                )
            if to_create:
                await ChatLimit.bulk_create(to_create, batch_size=batch_size)

        async with self._lock:
            for key, val in payloads.items():
                cur = self._cache.get(key)
                if cur is None or cur.time == val:
                    self._dirty.discard(key)


class ChatLimitManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = ChatLimitRepository()
        self.cache = ChatLimitCache(self.repo, self._cache)

    async def initialize(self):
        await self.cache.initialize()

    async def get(self, chat_id: int):
        return await self.cache.get(_make_cache_key(chat_id))

    async def edit_time(self, chat_id: int, time: int):
        if time == 0:
            return bool(await self.delete(chat_id))

        return await self.cache.edit(
            _make_cache_key(chat_id),
            time=time,
        )

    async def delete(self, chat_id: int) -> Optional[CachedChatLimitRow]:
        return await self.cache.remove(_make_cache_key(chat_id))
