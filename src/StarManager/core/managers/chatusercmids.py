from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, TypeAlias

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


CacheKey: TypeAlias = Tuple[int, int]
Cache: TypeAlias = Dict[CacheKey, _CachedChatUserCMIDs]


def _make_cache_key(uid: int, chat_id: int) -> CacheKey:
    return (uid, chat_id)


class ChatUserCMIDsRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def get_existing_cmids(self, uid: int, chat_id: int) -> Set[int]:
        return {
            row.cmid
            for row in await ChatUserCMIDs.filter(uid=uid, chat_id=chat_id).all()
        }

    async def clear(self):
        await ChatUserCMIDs.all().delete()


class ChatUserCMIDsCache(BaseCacheManager):
    def __init__(self, repo: ChatUserCMIDsRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        groups: Dict[CacheKey, List[int]] = defaultdict(list)
        async with self._lock:
            for row in await ChatUserCMIDs.all():
                key = _make_cache_key(row.uid, row.chat_id)
                groups[key].append(row.cmid)

            for key, cmids in groups.items():
                self._cache[key] = _CachedChatUserCMIDs.from_list(sorted(set(cmids)))
        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ):
        initial_data = initial_data or {"cmids": []}
        async with self._lock:
            if cache_key in self._cache:
                return
            existing = await self.repo.get_existing_cmids(*cache_key)
            if existing:
                self._cache[cache_key] = _CachedChatUserCMIDs.from_list(
                    sorted(set(existing))
                )
            else:
                self._cache[cache_key] = _CachedChatUserCMIDs.from_list(
                    initial_data.get("cmids", [])
                )

    async def get(self, cache_key: CacheKey):
        async with self._lock:
            obj = self._cache.get(cache_key)
            return tuple(obj.cmids) if obj else ()

    async def append(self, cache_key: CacheKey, cmid: int):
        await self._ensure_cached(cache_key, {"cmids": []})
        async with self._lock:
            lst = self._cache[cache_key].cmids
            if cmid in lst:
                return
            lst.append(cmid)
            self._dirty.add(cache_key)


    async def clear(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()
        await self.repo.clear()

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty_snapshot = set(self._dirty)
            payloads = {
                key: set(self._cache[key].cmids)
                for key in dirty_snapshot
                if key in self._cache
            }

        if not payloads:
            return

        items = list(payloads.items())
        try:
            unique_uids = {uid for uid, _ in payloads.keys()}
            rows = await ChatUserCMIDs.filter(uid__in=list(unique_uids)).all()

            existing_map = defaultdict(set)
            for row in rows:
                key = (row.uid, row.chat_id)
                if key in payloads:
                    existing_map[key].add(row.cmid)

            for i in range(0, len(items), batch_size):
                batch, to_create = items[i : i + batch_size], []

                for (uid, chat_id), cmids in batch:
                    for cmid in cmids - existing_map[_make_cache_key(uid, chat_id)]:
                        to_create.append(
                            ChatUserCMIDs(uid=uid, chat_id=chat_id, cmid=cmid)
                        )

                if to_create:
                    await ChatUserCMIDs.bulk_create(to_create, batch_size=batch_size)
        except Exception:
            from loguru import logger

            logger.exception("ChatUserCMIDs sync failed")
            return

        async with self._lock:
            self._dirty.difference_update(dirty_snapshot)


class ChatUserCMIDsManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo: ChatUserCMIDsRepository = ChatUserCMIDsRepository()
        self.cache: ChatUserCMIDsCache = ChatUserCMIDsCache(self.repo, self._cache)

        self.clear = self.cache.clear

    async def initialize(self):
        await self.cache.initialize()

    async def get_cmids(self, uid: int, chat_id: int) -> Tuple[int, ...]:
        return await self.cache.get(_make_cache_key(uid, chat_id))

    async def append_cmid(self, uid: int, chat_id: int, cmid: int):
        await self.cache.append(_make_cache_key(uid, chat_id), cmid)

    async def sync(self):
        await self.cache.sync()
