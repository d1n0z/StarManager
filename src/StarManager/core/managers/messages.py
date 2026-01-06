from copy import deepcopy
from dataclasses import MISSING, dataclass, fields
from typing import Any, Dict, Iterable, Optional, Set, Tuple, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import Messages


@dataclass
class CachedMessagesRow(BaseCachedModel):
    uid: int
    chat_id: int
    messages: int = 0


DEFAULTS = {
    f.name: f.default
    for f in fields(CachedMessagesRow)
    if f.default is not MISSING and f.name not in ("uid", "chat_id")
}


CacheKey: TypeAlias = Tuple[int, int]
Cache: TypeAlias = Dict[CacheKey, CachedMessagesRow]


def _make_cache_key(uid: int, chat_id: int) -> CacheKey:
    return (uid, chat_id)


class MessagesRepository(BaseRepository):
    async def ensure_record(
        self, uid: int, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[Messages, bool]:
        obj, created = await Messages.get_or_create(
            uid=uid, chat_id=chat_id, defaults=defaults
        )
        return obj, created

    async def get_record(self, uid: int, chat_id: int) -> Optional[Messages]:
        return await Messages.filter(uid=uid, chat_id=chat_id).first()


class MessagesCache(BaseCacheManager):
    def __init__(self, repo: MessagesRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await Messages.all():
                key = _make_cache_key(row.uid, row.chat_id)
                cached = CachedMessagesRow.from_model(row)
                self._cache[key] = cached

        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        async with self._lock:
            if cache_key in self._cache:
                return False

        uid, chat_id = cache_key
        model, created = await self.repo.ensure_record(
            uid,
            chat_id,
            defaults=DEFAULTS | (initial_data or {}),
        )
        cached = CachedMessagesRow.from_model(model)

        async with self._lock:
            self._cache[cache_key] = cached

        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedMessagesRow]:
        async with self._lock:
            row = self._cache.get(cache_key)
            return deepcopy(row) if row else None

    async def edit(self, cache_key: CacheKey, *, ensure: bool = True, **fields):
        if ensure:
            await self._ensure_cached(cache_key, fields)
        async with self._lock:
            if not ensure and cache_key not in self._cache:
                return False
            row = self._cache[cache_key]
            for k, v in fields.items():
                setattr(row, k, v)
            self._dirty.add(cache_key)
        return True

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            payloads = {k: self._cache[k] for k in dirty if k in self._cache}

        if not payloads:
            return

        items = list(payloads.items())
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            uids = list({k[0] for k, _ in batch})

            existing = await Messages.filter(uid__in=uids)
            existing_map = {_make_cache_key(r.uid, r.chat_id): r for r in existing}

            to_update, to_create = [], []
            for key, cached in batch:
                if key in existing_map:
                    row = existing_map[key]
                    dirty = False
                    for field in CachedMessagesRow.__dataclass_fields__:
                        val = getattr(cached, field)
                        if getattr(row, field) != val:
                            setattr(row, field, val)
                            dirty = True
                    if dirty:
                        to_update.append(row)
                else:
                    data = cached.__dict__.copy()
                    data.update({"uid": key[0], "chat_id": key[1]})
                    to_create.append(Messages(**data))

            if to_update:
                update_fields = list(CachedMessagesRow.__dataclass_fields__.keys())
                await Messages.bulk_update(
                    to_update,
                    fields=[f for f in update_fields if f not in ("chat_id", "uid")],
                    batch_size=batch_size,
                )
            if to_create:
                await Messages.bulk_create(to_create, batch_size=batch_size)

        async with self._lock:
            for ck, old_val in payloads.items():
                cur = self._cache.get(ck)
                if cur is None:
                    self._dirty.discard(ck)
                    continue
                if cur.__dict__ == old_val.__dict__:
                    self._dirty.discard(ck)

    async def increment_messages(self, cache_key: CacheKey):
        await self._ensure_cached(cache_key)
        async with self._lock:
            self._cache[cache_key].messages += 1
            self._dirty.add(cache_key)

    async def top_messages_for_chat(
        self,
        chat_id: int,
        member_ids: Iterable[int],
        exclude_ids: Optional[Iterable[int]] = None,
        limit: int = 10,
    ):
        exclude_set = set(exclude_ids or ())
        rows = []
        async with self._lock:
            for uid in member_ids:
                if (not isinstance(uid, int)) or uid <= 0 or uid in exclude_set:
                    continue
                key = _make_cache_key(uid, chat_id)
                cached = self._cache.get(key)
                if cached is None:
                    continue
                if getattr(cached, "messages", 0) > 0:
                    rows.append(deepcopy(cached))

        rows.sort(key=lambda r: r.messages, reverse=True)
        return rows[:limit] if len(rows) > limit else rows


class MessagesManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = MessagesRepository()
        self.cache = MessagesCache(self.repo, self._cache)

        self.top_messages_for_chat = self.cache.top_messages_for_chat

    async def initialize(self):
        await self.cache.initialize()

    async def get(self, uid: int, chat_id: int) -> Optional[CachedMessagesRow]:
        return await self.cache.get(_make_cache_key(uid, chat_id))

    async def get_user_messages(self, uid: int, chat_id: int):
        u = await self.get(uid, chat_id)
        return u.messages if u else 0

    async def increment_messages(self, uid: int, chat_id: int):
        return await self.cache.increment_messages(_make_cache_key(uid, chat_id))

    async def top_in_chat_excluding(
        self,
        chat_id: int,
        member_ids: Iterable[int],
        exclude_ids: Optional[Iterable[int]] = None,
        limit: int = 10,
    ):
        return await self.cache.top_messages_for_chat(
            chat_id, member_ids, exclude_ids, limit
        )
