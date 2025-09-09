import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from tortoise.expressions import Q

from StarManager.core.managers.base import BaseCacheManager, BaseManager, BaseRepository, BaseCachedModel
from StarManager.core.tables import ChatUserCMIDs


@dataclass
class _CachedChatUserCMIDs(BaseCachedModel):
    cmids: List[int]


class ChatUserCMIDsRepository(BaseRepository):
    def __init__(self, items: List[ChatUserCMIDs]):
        super().__init__()
        self._items = items

    async def ensure_record(
        self, uid: int, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> ChatUserCMIDs:
        defaults = defaults or {"cmids": []}
        obj, _created = await ChatUserCMIDs.get_or_create(
            uid=uid, chat_id=chat_id, defaults=defaults
        )
        async with self._lock:
            if obj not in self._items:
                self._items.append(obj)
        return obj

    async def get_record(self, uid: int, chat_id: int) -> Optional[ChatUserCMIDs]:
        async with self._lock:
            return next(
                (i for i in self._items if i.uid == uid and i.chat_id == chat_id),
                None,
            )


class ChatUserCMIDsCache(BaseCacheManager):
    def __init__(self, repo: ChatUserCMIDsRepository, items: List[ChatUserCMIDs]):
        super().__init__()
        self._cache: Dict[Tuple[int, int], _CachedChatUserCMIDs] = {}
        self._dirty: Set[Tuple[int, int]] = set()
        self.repo = repo
        self._items = items

    def make_cache_key(self, uid: int, chat_id: int) -> Tuple[int, int]:
        return (uid, chat_id)

    async def initialize(self):
        async with self._lock:
            for row in self._items:
                key = self.make_cache_key(row.uid, row.chat_id)
                self._cache[key] = _CachedChatUserCMIDs.from_model(row)
        await super().initialize()

    async def _ensure_cached(
        self, cache_key: Tuple[int, int], initial_data: Optional[Dict[str, Any]] = None
    ):
        initial_data = initial_data or {"cmids": []}
        async with self._lock:
            if cache_key in self._cache:
                return

        uid, chat_id = cache_key
        model = await self.repo.ensure_record(uid, chat_id, defaults=initial_data)
        async with self._lock:
            self._cache[cache_key] = _CachedChatUserCMIDs.from_model(model)

    async def get(self, cache_key: Tuple[int, int]) -> Tuple[int, ...]:
        async with self._lock:
            obj = self._cache.get(cache_key)
            return tuple(obj.cmids) if obj else ()

    async def append(self, cache_key: Tuple[int, int], cmid: int):
        await self._ensure_cached(cache_key, {"cmids": []})
        async with self._lock:
            if cmid in self._cache[cache_key].cmids:
                return
            self._cache[cache_key].cmids.append(cmid)
            self._dirty.add(cache_key)

    async def sync(self):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            payloads = {
                (uid, chat_id): self._cache[(uid, chat_id)].cmids
                for uid, chat_id in dirty
                if (uid, chat_id) in self._cache
            }

        query = Q()
        for uid, chat_id in payloads.keys():
            query |= Q(uid=uid, chat_id=chat_id)
        existing = await ChatUserCMIDs.filter(query) if query else []
        existing = {(row.uid, row.chat_id): row for row in existing}

        to_update, to_create = [], []
        for (uid, chat_id), cmids in payloads.items():
            if (uid, chat_id) in existing:
                row = existing[(uid, chat_id)]
                row.cmids = cmids
                to_update.append(row)
            else:
                to_create.append(ChatUserCMIDs(uid=uid, chat_id=chat_id, cmids=cmids))

        if to_update:
            await ChatUserCMIDs.bulk_update(to_update, fields=["cmids"])
        if to_create:
            await ChatUserCMIDs.bulk_create(to_create)

        async with self._lock:
            self._dirty.difference_update(dirty)


class ChatUserCMIDsManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._items: List[ChatUserCMIDs] = []
        self.repo: ChatUserCMIDsRepository = ChatUserCMIDsRepository(self._items)
        self.cache: ChatUserCMIDsCache = ChatUserCMIDsCache(self.repo, self._items)

    async def initialize(self):
        rows = await ChatUserCMIDs.all()
        async with self._lock:
            self._items.extend(rows)
        await self.cache.initialize()

    def make_key(self, uid: int, chat_id: int) -> Tuple[int, int]:
        return self.cache.make_cache_key(uid, chat_id)

    async def get_cmids(self, uid: int, chat_id: int) -> Tuple[int, ...]:
        return await self.cache.get(self.make_key(uid, chat_id))

    async def append_cmid(self, uid: int, chat_id: int, cmid: int):
        await self.cache.append(self.make_key(uid, chat_id), cmid)

    async def sync(self):
        await self.cache.sync()
