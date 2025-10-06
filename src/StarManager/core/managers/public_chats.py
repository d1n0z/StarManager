import asyncio
import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, TypeAlias

from StarManager.core.config import api, settings
from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import ChatNames, PublicChats, UpCommandLogs

DEFAULTS = {
    "premium": False,
    "last_up": 0,
    "isopen": False,
}


CacheKey: TypeAlias = int
UpCacheKey: TypeAlias = int


@dataclass
class _CachedPublicChatObject(BaseCachedModel):
    premium: bool
    last_up: int
    isopen: bool
    members_count: int


@dataclass
class _CachedUpLog(BaseCachedModel):
    timestamp: int


@dataclass
class _CachedPublicChat(BaseCachedModel):
    chat: _CachedPublicChatObject
    uplogs: Dict[UpCacheKey, _CachedUpLog]


Cache: TypeAlias = Dict[CacheKey, _CachedPublicChat]


def _make_cache_key(chat_id: int) -> CacheKey:
    return chat_id


def _make_up_cache_key(uid: int) -> UpCacheKey:
    return uid


class PublicChatsRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def ensure_record(
        self, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[PublicChats, bool]:
        defaults = defaults or {
            "premium": False,
            "last_up": 0,
            "isopen": False,
            "members_count": 0,
        }
        obj, created = await PublicChats.get_or_create(
            chat_id=chat_id,
            defaults=(
                defaults | {k: v for k, v in DEFAULTS.items() if k not in defaults}
            ),
        )
        if created:
            try:
                vk_chat = await api.messages.get_conversations_by_id(
                    peer_ids=[2000000000 + chat_id]
                )
                if (
                    not vk_chat
                    or not vk_chat.items
                    or not vk_chat.items[0].chat_settings
                    or not (
                        member_count := vk_chat.items[0].chat_settings.members_count
                    )
                ):
                    raise ValueError
                obj.members_count = member_count
            except Exception:
                pass
            else:
                await obj.save()
        return obj, created

    async def get_record(self, chat_id: int) -> Optional[PublicChats]:
        return await PublicChats.filter(chat_id=chat_id).first()

    async def delete_record(self, chat_id: int):
        await PublicChats.filter(chat_id=chat_id).delete()


class UpCommandLogsRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def get_logs_for_chat(self, chat_id: int) -> List[UpCommandLogs]:
        return await UpCommandLogs.filter(chat_id=chat_id)

    async def get_logs_by_pairs(
        self, pairs: List[Tuple[int, int]]
    ) -> List[UpCommandLogs]:
        if not pairs:
            return []
        chat_ids = list({p[0] for p in pairs})
        candidates = await UpCommandLogs.filter(chat_id__in=chat_ids)
        wanted = set(pairs)
        return [r for r in candidates if (r.chat_id, r.uid) in wanted]

    async def ensure_log(
        self, chat_id: int, uid: int, timestamp: int
    ) -> Tuple[UpCommandLogs, bool]:
        obj, created = await UpCommandLogs.get_or_create(
            chat_id=chat_id, uid=uid, defaults={"timestamp": timestamp}
        )
        if not created:
            if obj.timestamp != timestamp:
                obj.timestamp = timestamp
                await obj.save()
        return obj, created

    async def delete_logs_for_chat(self, chat_id: int):
        await UpCommandLogs.filter(chat_id=chat_id).delete()

    async def delete_log(self, chat_id: int, uid: int):
        await UpCommandLogs.filter(chat_id=chat_id, uid=uid).delete()


class PublicChatsCache(BaseCacheManager):
    def __init__(
        self,
        repo: PublicChatsRepository,
        uplog_repo: UpCommandLogsRepository,
        cache: Cache,
    ):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo
        self.uplog_repo = uplog_repo

    async def initialize(self):
        self._lock = asyncio.Lock()

        rows = await PublicChats.all()
        logs = await UpCommandLogs.all()

        async with self._lock:
            for row in rows:
                key = _make_cache_key(row.chat_id)
                self._cache[key] = _CachedPublicChat(
                    chat=_CachedPublicChatObject(
                        premium=bool(row.premium),
                        last_up=int(row.last_up or 0),
                        isopen=bool(row.isopen),
                        members_count=int(row.members_count or 0),
                    ),
                    uplogs={},
                )

            for log in logs:
                key = _make_cache_key(log.chat_id)
                if key not in self._cache:
                    self._cache[key] = _CachedPublicChat(
                        chat=_CachedPublicChatObject(
                            premium=False, last_up=0, isopen=False, members_count=0
                        ),
                        uplogs={},
                    )
                self._cache[key].uplogs[_make_up_cache_key(log.uid)] = _CachedUpLog(
                    timestamp=int(log.timestamp or 0)
                )

        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_chat_data: Optional[Dict[str, Any]] = None
    ):
        async with self._lock:
            if cache_key in self._cache:
                return False

        chat_id = cache_key
        defaults = initial_chat_data or DEFAULTS
        model, created = await self.repo.ensure_record(chat_id, defaults=defaults)
        async with self._lock:
            self._cache[cache_key] = _CachedPublicChat(
                chat=_CachedPublicChatObject(
                    premium=bool(model.premium),
                    last_up=int(model.last_up or 0),
                    isopen=bool(model.isopen),
                    members_count=int(model.members_count or 0),
                ),
                uplogs={},
            )
        return created

    async def get(self, cache_key: CacheKey, field: str = "chat"):
        async with self._lock:
            obj = self._cache.get(cache_key)
        if obj is None:
            return None
        if field == "chat":
            return obj.chat
        return getattr(obj.chat, field, None)

    async def edit(self, cache_key: CacheKey, **fields):
        await self._ensure_cached(cache_key, initial_chat_data=fields)
        async with self._lock:
            for field, value in fields.items():
                if hasattr(self._cache[cache_key].chat, field):
                    setattr(self._cache[cache_key].chat, field, value)
            self._dirty.add(cache_key)

    async def add_uplog(self, cache_key: CacheKey, uid: int, timestamp: int):
        await self._ensure_cached(cache_key)
        async with self._lock:
            self._cache[cache_key].uplogs[_make_up_cache_key(uid)] = _CachedUpLog(
                timestamp=timestamp
            )
            self._dirty.add(cache_key)

    async def get_uplog(self, cache_key: CacheKey, uid: int) -> Optional[_CachedUpLog]:
        async with self._lock:
            obj = self._cache.get(cache_key)
            if not obj:
                return None
            return obj.uplogs.get(_make_up_cache_key(uid))

    async def remove(self, cache_key: CacheKey):
        async with self._lock:
            if cache_key in self._cache:
                self._dirty.discard(cache_key)
                del self._cache[cache_key]
        chat_id = cache_key
        await self.uplog_repo.delete_logs_for_chat(chat_id)
        await self.repo.delete_record(chat_id)

    async def sync_from_db(self, load_uplogs: bool = True):
        rows = await PublicChats.all()
        logs = await UpCommandLogs.all() if load_uplogs else []

        new_cache: Cache = {}
        for row in rows:
            key = _make_cache_key(row.chat_id)
            new_cache[key] = _CachedPublicChat(
                chat=_CachedPublicChatObject(
                    premium=bool(row.premium),
                    last_up=int(row.last_up or 0),
                    isopen=bool(row.isopen),
                    members_count=int(row.members_count or 0),
                ),
                uplogs={},
            )

        if load_uplogs:
            for log in logs:
                key = _make_cache_key(log.chat_id)
                if key not in new_cache:
                    new_cache[key] = _CachedPublicChat(
                        chat=_CachedPublicChatObject(
                            premium=False, last_up=0, isopen=False, members_count=0
                        ),
                        uplogs={},
                    )
                new_cache[key].uplogs[_make_up_cache_key(log.uid)] = _CachedUpLog(
                    timestamp=int(log.timestamp or 0)
                )

        async with self._lock:
            dirty_snapshot = set(self._dirty)

            for cid in dirty_snapshot:
                cur = self._cache.get(cid)
                if cur is not None:
                    new_cache[cid] = copy.deepcopy(cur)

            self._cache.clear()
            self._cache.update(new_cache)

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty_snapshot = set(self._dirty)
            payloads = {
                cid: copy.deepcopy(self._cache[cid])
                for cid in dirty_snapshot
                if cid in self._cache
            }

        if not payloads:
            return

        items = list(payloads.items())
        try:
            # Sync PublicChats in batches
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                chat_ids = [cid for cid, _ in batch]

                existing_rows = await PublicChats.filter(chat_id__in=chat_ids)
                existing_map = {row.chat_id: row for row in existing_rows}

                to_update_chats, to_create_chats = [], []
                for cid, cached in batch:
                    if cid in existing_map:
                        row = existing_map[cid]
                        dirty = False
                        # fields on PublicChats we care about
                        for field in ("premium", "last_up", "isopen"):
                            val = getattr(cached.chat, field)
                            # row fields types: premium(bool), last_up(int), isopen(bool)
                            if getattr(row, field) != val:
                                setattr(row, field, val)
                                dirty = True
                        if dirty:
                            to_update_chats.append(row)
                    else:
                        to_create_chats.append(
                            PublicChats(
                                chat_id=cid,
                                premium=cached.chat.premium,
                                last_up=cached.chat.last_up,
                                isopen=cached.chat.isopen,
                            )
                        )

                if to_update_chats:
                    await PublicChats.bulk_update(
                        to_update_chats,
                        fields=["premium", "last_up", "isopen"],
                        batch_size=batch_size,
                    )
                if to_create_chats:
                    await PublicChats.bulk_create(
                        to_create_chats, batch_size=batch_size
                    )

                # Now handle UpCommandLogs for this batch
                # Collect all (chat_id, uid) pairs we need to sync
                pairs = []
                for cid, cached in batch:
                    for uid_key, uplog in cached.uplogs.items():
                        pairs.append((cid, uid_key))

                # fetch existing logs for these pairs
                existing_logs = await self.uplog_repo.get_logs_by_pairs(pairs)
                existing_map = {(r.chat_id, r.uid): r for r in existing_logs}

                to_update_logs, to_create_logs = [], []
                for cid, cached in batch:
                    for uid_key, uplog in cached.uplogs.items():
                        key = (cid, uid_key)
                        if key in existing_map:
                            row = existing_map[key]
                            if row.timestamp != uplog.timestamp:
                                row.timestamp = uplog.timestamp
                                to_update_logs.append(row)
                        else:
                            to_create_logs.append(
                                UpCommandLogs(
                                    chat_id=cid, uid=uid_key, timestamp=uplog.timestamp
                                )
                            )

                if to_update_logs:
                    await UpCommandLogs.bulk_update(
                        to_update_logs, fields=["timestamp"], batch_size=batch_size
                    )
                if to_create_logs:
                    await UpCommandLogs.bulk_create(
                        to_create_logs, batch_size=batch_size
                    )

        except Exception:
            from loguru import logger

            logger.exception("PublicChats sync failed")
            return

        async with self._lock:
            for cid, old_val in payloads.items():
                cur = self._cache.get(cid)
                if cur is None:
                    self._dirty.discard(cid)
                    continue
                if cur.__dict__ == old_val.__dict__:
                    self._dirty.discard(cid)


class PublicChatsManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo: PublicChatsRepository = PublicChatsRepository()
        self.uplog_repo: UpCommandLogsRepository = UpCommandLogsRepository()
        self.cache: PublicChatsCache = PublicChatsCache(
            self.repo, self.uplog_repo, self._cache
        )

    async def initialize(self):
        await self.cache.initialize()

    async def ensure_chat(
        self, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ):
        return await self.repo.ensure_record(chat_id, defaults=defaults)

    async def get_chat(self, chat_id: int) -> Optional[_CachedPublicChatObject]:
        return await self.cache.get(_make_cache_key(chat_id), field="chat")

    async def edit_chat(self, chat_id: int, **fields):
        await self.cache.edit(_make_cache_key(chat_id), **fields)

    async def remove_chat(self, chat_id: int):
        await self.cache.remove(_make_cache_key(chat_id))

    async def can_user_up(
        self, chat_id: int, uid: int, now_ts: Optional[int] = None
    ) -> Tuple[bool, int]:
        if now_ts is None:
            import time

            now_ts = int(time.time())
        else:
            now_ts = int(now_ts)

        await self.cache._ensure_cached(_make_cache_key(chat_id))
        uplog = await self.cache.get_uplog(_make_cache_key(chat_id), uid)
        if not uplog:
            return True, 0
        diff = now_ts - int(uplog.timestamp)
        if diff >= 86400:
            return True, 0
        return False, 86400 - diff

    async def do_up(
        self, chat_id: int, uid: int, now_ts: Optional[int] = None
    ) -> Tuple[bool, Optional[int]]:
        try:
            import time

            now_ts = now_ts or int(time.time())
        except Exception:
            now_ts = now_ts or int(asyncio.get_event_loop().time())

        await self.cache._ensure_cached(_make_cache_key(chat_id))
        chat_obj = await self.get_chat(chat_id)
        if not chat_obj:
            return False, None

        if not chat_obj.premium:
            return False, None

        allowed, remaining = await self.can_user_up(chat_id, uid, now_ts=now_ts)
        if not allowed:
            return False, remaining

        await self.cache.edit(_make_cache_key(chat_id), last_up=now_ts)
        await self.cache.add_uplog(_make_cache_key(chat_id), uid, now_ts)
        return True, None

    async def get_regular_chats(self) -> List[Tuple[int, _CachedPublicChatObject]]:
        async with self.cache._lock:
            return [
                (cid, copy.deepcopy(item.chat))
                for cid, item in self._cache.items()
                if item.chat.isopen
            ]

    async def count_regular_chats(self) -> int:
        async with self.cache._lock:
            return sum(1 for data in self._cache.values() if data.chat.isopen)

    async def get_sorted_premium_chats(
        self,
    ) -> List[Tuple[int, _CachedPublicChatObject]]:
        async with self.cache._lock:
            premium_chats = [
                (cid, copy.deepcopy(item.chat))
                for cid, item in self._cache.items()
                if item.chat.isopen and item.chat.premium
            ]
        return sorted(premium_chats, key=lambda x: x[1].last_up, reverse=True)

    async def count_premium_chats(self) -> int:
        async with self.cache._lock:
            return sum(
                1
                for data in self._cache.values()
                if data.chat.isopen and data.chat.premium
            )

    async def edit_premium(self, chat_id: int, make_premium: bool):
        await self.ensure_chat(chat_id)
        await self.edit_chat(chat_id, premium=make_premium)

    async def get_chats_top(
        self, chats: List[Tuple[int, _CachedPublicChatObject]]
    ):  # TODO: merge chatname and publicchats or add new cache
        counter = 0
        res = []
        for chat in chats:
            try:
                if chatname := await ChatNames.filter(chat_id=chat[0]).first():
                    chatname = chatname.name
                else:
                    chatname = await api.messages.get_conversations_by_id(
                        peer_ids=[chat[0] + 2000000000]
                    )
                    chatname = chatname.items[0].chat_settings
                    if not chatname or not chatname.title:
                        counter -= 1
                        continue
                    chatname = chatname.title
                    await ChatNames.create(chat_id=chat[0], name=chatname)
                if not chatname:
                    counter -= 1
                    continue
            except Exception:
                counter -= 1
                continue
            try:
                if (
                    not (
                        invite_link := (
                            await api.messages.get_invite_link(
                                peer_id=chat[0] + 2000000000,
                                reset=False,
                                group_id=settings.vk.group_id,
                            )
                        )
                    )
                    or not invite_link.link
                ):
                    counter -= 1
                    continue
            except Exception:
                continue
            res.append((invite_link.link, chat[1].members_count, chatname))
        return res, counter

    async def sync(self):
        await self.cache.sync()
