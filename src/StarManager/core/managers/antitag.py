from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Set, Tuple, TypeAlias, List

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import Antitag


@dataclass
class CachedAntitagRow(BaseCachedModel):
    uid: int
    chat_id: int


CacheKey: TypeAlias = Tuple[int, int]  # (uid, chat_id)
Cache: TypeAlias = Dict[CacheKey, CachedAntitagRow]


def _make_cache_key(uid: int, chat_id: int) -> CacheKey:
    return (uid, chat_id)


class AntitagRepository(BaseRepository):
    async def ensure_record(self, uid: int, chat_id: int) -> Tuple[Antitag, bool]:
        obj, created = await Antitag.get_or_create(uid=uid, chat_id=chat_id)
        return obj, created

    async def get_record(self, uid: int, chat_id: int) -> Optional[Antitag]:
        return await Antitag.filter(uid=uid, chat_id=chat_id).first()

    async def delete_record(self, uid: int, chat_id: int):
        await Antitag.filter(uid=uid, chat_id=chat_id).delete()

    async def delete_multiple(self, keys: Iterable[CacheKey]):
        pairs = list(keys)
        if not pairs:
            return
        batch = []
        for uid, chat_id in pairs:
            batch.append((uid, chat_id))
            if len(batch) >= 500:
                await Antitag.filter(
                    tuple__in=[{"uid": u, "chat_id": c} for u, c in batch]
                ).delete()
                batch.clear()
        if batch:
            await Antitag.filter(
                tuple__in=[{"uid": u, "chat_id": c} for u, c in batch]
            ).delete()

    async def get_records_for_chat(self, chat_id: int) -> List[Antitag]:
        return await Antitag.filter(chat_id=chat_id).all()

    async def get_existing_keys(self, keys: Iterable[CacheKey]) -> Set[CacheKey]:
        keys = list(keys)
        if not keys:
            return set()
        existing: Set[CacheKey] = set()
        by_chat: Dict[int, List[int]] = {}
        for uid, chat_id in keys:
            by_chat.setdefault(chat_id, []).append(uid)

        for chat_id, uids in by_chat.items():
            rows = await Antitag.filter(chat_id=chat_id, uid__in=uids).all()
            for r in rows:
                existing.add((r.uid, r.chat_id))
        return existing


class AntitagCache(BaseCacheManager):
    def __init__(self, repo: AntitagRepository, cache: Cache):
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

            for row in await Antitag.all():
                key = _make_cache_key(row.uid, row.chat_id)
                cached = CachedAntitagRow.from_model(row)
                self._cache[key] = cached

        await super().initialize()

    async def _ensure_cached(self, cache_key: CacheKey) -> bool:
        async with self._lock:
            if cache_key in self._cache:
                return False

        uid, chat_id = cache_key
        model, created = await self.repo.ensure_record(uid, chat_id)
        cached = CachedAntitagRow.from_model(model)
        async with self._lock:
            self._cache[cache_key] = cached
            if created:
                self._to_add.discard(cache_key)
            else:
                self._to_add.discard(cache_key)
        return created

    async def exists(self, cache_key: CacheKey) -> bool:
        async with self._lock:
            return cache_key in self._cache

    async def get(self, cache_key: CacheKey) -> Optional[CachedAntitagRow]:
        async with self._lock:
            row = self._cache.get(cache_key)
            return deepcopy(row) if row else None

    async def add(self, cache_key: CacheKey):
        async with self._lock:
            if cache_key in self._cache:
                return False
            uid, chat_id = cache_key
            self._cache[cache_key] = CachedAntitagRow(uid=uid, chat_id=chat_id)
            if cache_key in self._to_remove:
                self._to_remove.discard(cache_key)
            else:
                self._to_add.add(cache_key)
        return True

    async def remove(self, cache_key: CacheKey):
        async with self._lock:
            if cache_key not in self._cache:
                return False
            del self._cache[cache_key]
            if cache_key in self._to_add:
                self._to_add.discard(cache_key)
            else:
                self._to_remove.add(cache_key)
        return True

    async def get_for_chat(self, chat_id: int) -> List[int]:
        async with self._lock:
            return [c.uid for c in self._cache.values() if c.chat_id == chat_id]

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
            existing = await self.repo.get_existing_keys(keys)
            to_create = [k for k in keys if k not in existing]
            items = []
            for uid, chat_id in to_create:
                items.append(Antitag(uid=uid, chat_id=chat_id))

            for i in range(0, len(items), batch_size):
                chunk = items[i : i + batch_size]
                try:
                    if chunk:
                        await Antitag.bulk_create(chunk, batch_size=batch_size)
                except Exception:
                    pass

        async with self._lock:
            for k in to_add:
                self._to_add.discard(k)
            for k in to_remove:
                self._to_remove.discard(k)

    async def delete_all_for_chat(self, chat_id: int):
        async with self._lock:
            to_remove = [k for k in self._cache if k[1] == chat_id]
            for k in to_remove:
                del self._cache[k]
                if k in self._to_add:
                    self._to_add.discard(k)
                else:
                    self._to_remove.add(k)

    async def exists_many(self, chat_id: int, uids: Iterable[int]) -> Set[int]:
        uids = set(uids)
        if not uids:
            return set()

        async with self._lock:
            return {uid for uid in uids if (uid, chat_id) in self._cache}


class AntitagManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = AntitagRepository()
        self.cache = AntitagCache(self.repo, self._cache)

        self.exists_many = self.cache.exists_many
        self.get_for_chat = self.cache.get_for_chat
        self.delete_all_for_chat = self.cache.delete_all_for_chat

    async def initialize(self):
        await self.cache.initialize()

    async def exists(self, uid: int, chat_id: int) -> bool:
        return await self.cache.exists(_make_cache_key(uid, chat_id))

    async def get(self, uid: int, chat_id: int) -> Optional[CachedAntitagRow]:
        return await self.cache.get(_make_cache_key(uid, chat_id))

    async def add(self, uid: int, chat_id: int):
        return await self.cache.add(_make_cache_key(uid, chat_id))

    async def remove(self, uid: int, chat_id: int):
        return await self.cache.remove(_make_cache_key(uid, chat_id))
