from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from tortoise.expressions import Q

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import ChatUserCMIDs


@dataclass
class _CachedChatUserCMIDs(BaseCachedModel):
    cmids: List[int]

    @classmethod
    def from_list(cls, cmids_list: List[int]):
        return cls(cmids=list(cmids_list))


class ChatUserCMIDsRepository(BaseRepository):
    def __init__(self, items: List[ChatUserCMIDs]):
        super().__init__()
        self._items = items

    async def get_existing_cmids(self, uid: int, chat_id: int) -> Set[int]:
        async with self._lock:
            return {
                row.cmid
                for row in self._items
                if row.uid == uid and row.chat_id == chat_id
            }


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
        groups: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        async with self._lock:
            for row in self._items:
                key = self.make_cache_key(row.uid, row.chat_id)
                groups[key].append(row.cmid)

            for key, cmids in groups.items():
                self._cache[key] = _CachedChatUserCMIDs.from_list(sorted(set(cmids)))
        await super().initialize()

    async def _ensure_cached(
        self, cache_key: Tuple[int, int], initial_data: Optional[Dict[str, Any]] = None
    ):
        initial_data = initial_data or {"cmids": []}
        async with self._lock:
            if cache_key in self._cache:
                return
            uid, chat_id = cache_key
            existing = [
                row.cmid
                for row in self._items
                if row.uid == uid and row.chat_id == chat_id
            ]
            if existing:
                self._cache[cache_key] = _CachedChatUserCMIDs.from_list(
                    sorted(set(existing))
                )
            else:
                self._cache[cache_key] = _CachedChatUserCMIDs.from_list(
                    initial_data.get("cmids", [])
                )

    async def get(self, cache_key: Tuple[int, int]) -> Tuple[int, ...]:
        async with self._lock:
            obj = self._cache.get(cache_key)
            return tuple(obj.cmids) if obj else ()

    async def append(self, cache_key: Tuple[int, int], cmid: int):
        await self._ensure_cached(cache_key, {"cmids": []})
        async with self._lock:
            lst = self._cache[cache_key].cmids
            if cmid in lst:
                return
            lst.append(cmid)
            self._dirty.add(cache_key)

    async def sync(self):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            # snapshot payloads
            payloads = {
                key: list(self._cache[key].cmids) for key in dirty if key in self._cache
            }
            if not payloads:
                return

        query = Q()
        for uid, chat_id in payloads.keys():
            query |= Q(uid=uid, chat_id=chat_id)
        existing_rows = await ChatUserCMIDs.filter(query)
        existing_map: Dict[Tuple[int, int], Set[int]] = defaultdict(set)
        for row in existing_rows:
            existing_map[(row.uid, row.chat_id)].add(row.cmid)

        to_create: List[ChatUserCMIDs] = []
        for (uid, chat_id), cmids in payloads.items():
            present_set = existing_map.get((uid, chat_id), set())
            new_cmids = set(cmids) - present_set
            for cm in new_cmids:
                to_create.append(ChatUserCMIDs(uid=uid, chat_id=chat_id, cmid=cm))

        if to_create:
            BATCH = 5000
            for i in range(0, len(to_create), BATCH):
                await ChatUserCMIDs.bulk_create(to_create[i : i + BATCH])
            async with self._lock:
                self._items.extend(to_create)

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
