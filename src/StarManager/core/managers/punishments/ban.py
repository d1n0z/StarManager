from ast import literal_eval
from collections import defaultdict
from copy import deepcopy
from dataclasses import MISSING, dataclass, fields
from datetime import datetime
from typing import Any, Dict, Optional, Set, Tuple, TypeAlias

from StarManager.core.config import settings
from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import Ban


@dataclass
class CachedBanRow(BaseCachedModel):
    uid: int
    chat_id: int = 0
    ban: int = 0
    last_bans_times: Optional[str] = None
    last_bans_causes: Optional[str] = None
    last_bans_names: Optional[str] = None
    last_bans_dates: Optional[str] = None


DEFAULTS = {
    f.name: f.default
    for f in fields(CachedBanRow)
    if f.default is not MISSING and f.name not in ("uid", "chat_id")
}


CacheKey: TypeAlias = Tuple[int, int]
Cache: TypeAlias = Dict[CacheKey, CachedBanRow]


def _make_cache_key(uid: int, chat_id: int) -> CacheKey:
    return (uid, chat_id)


class BanRepository(BaseRepository):
    async def ensure_record(
        self, uid: int, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[Ban, bool]:
        obj, created = await Ban.get_or_create(
            uid=uid, chat_id=chat_id, defaults=defaults
        )
        return obj, created

    async def get_record(self, uid: int, chat_id: int) -> Optional[Ban]:
        return await Ban.filter(uid=uid, chat_id=chat_id).first()

    async def delete_record(self, uid: int, chat_id: int):
        await Ban.filter(uid=uid, chat_id=chat_id).delete()

    async def delete_chat(self, chat_id: int):
        await Ban.filter(chat_id=chat_id).delete()


class BanCache(BaseCacheManager):
    def __init__(self, repo: BanRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

        self._index_by_chat_id: Dict[int, Set[CacheKey]] = defaultdict(set)

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()
            self._index_by_chat_id.clear()

            for row in await Ban.all():
                key = _make_cache_key(row.uid, row.chat_id)
                cached = CachedBanRow.from_model(row)
                self._cache[key] = cached
                self._index_by_chat_id[row.chat_id].add(key)

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
        cached = CachedBanRow.from_model(model)

        async with self._lock:
            self._cache[cache_key] = cached
            self._index_by_chat_id[chat_id].add(cache_key)

        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedBanRow]:
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
            self._index_by_chat_id[cache_key[1]].add(cache_key)
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

            existing = await Ban.filter(uid__in=uids)
            existing_map = {_make_cache_key(r.uid, r.chat_id): r for r in existing}

            to_update, to_create = [], []
            for key, cached in batch:
                if key in existing_map:
                    row = existing_map[key]
                    dirty = False
                    for field in CachedBanRow.__dataclass_fields__:
                        val = getattr(cached, field)
                        if getattr(row, field) != val:
                            setattr(row, field, val)
                            dirty = True
                    if dirty:
                        to_update.append(row)
                else:
                    data = cached.__dict__.copy()
                    data.update({"uid": key[0], "chat_id": key[1]})
                    to_create.append(Ban(**data))

            if to_update:
                update_fields = list(CachedBanRow.__dataclass_fields__.keys())
                await Ban.bulk_update(
                    to_update,
                    fields=[f for f in update_fields if f not in ("chat_id", "uid")],
                    batch_size=batch_size,
                )
            if to_create:
                await Ban.bulk_create(to_create, batch_size=batch_size)

        async with self._lock:
            for ck, old_val in payloads.items():
                cur = self._cache.get(ck)
                if cur is None:
                    self._dirty.discard(ck)
                    continue
                if cur.__dict__ == old_val.__dict__:
                    self._dirty.discard(ck)

    async def get_all(self, chat_id: int):
        async with self._lock:
            return [self._cache[key] for key in self._index_by_chat_id[chat_id]]

    async def del_all(self, chat_id: int):
        async with self._lock:
            delete_keys = self._index_by_chat_id[chat_id]
            for key in delete_keys:
                del self._cache[key]
        await self.repo.delete_chat(chat_id)

    async def unban_all(self, chat_id: int):
        async with self._lock:
            uids = []
            unban_keys = self._index_by_chat_id[chat_id]
        for key in unban_keys:
            if await self.edit(key, ban=0, ensure=False):
                uids.append(key[1])
        return uids


class BanManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = BanRepository()
        self.cache = BanCache(self.repo, self._cache)

        self.get_all = self.cache.get_all
        self.del_all = self.cache.del_all
        self.unban_all = self.cache.unban_all

    async def initialize(self):
        await self.cache.initialize()

    async def get(self, uid: int, chat_id: int) -> Optional[CachedBanRow]:
        return await self.cache.get(_make_cache_key(uid, chat_id))

    async def ban(
        self,
        uid: int,
        chat_id: int,
        ban_for: int,
        reason: Optional[str] = None,
        by_name: str = f"[club{-settings.vk.group_id}|Star Manager]",
    ):
        ms = await self.get(uid, chat_id)
        if ms is not None:
            ban_times = literal_eval(ms.last_bans_times) if ms.last_bans_times else []
            ban_causes = (
                literal_eval(ms.last_bans_causes) if ms.last_bans_causes else []
            )
            ban_names = literal_eval(ms.last_bans_names) if ms.last_bans_names else []
            ban_dates = literal_eval(ms.last_bans_dates) if ms.last_bans_dates else []
        else:
            ban_times, ban_causes, ban_names, ban_dates = [], [], [], []

        now = datetime.now()
        ban_times.append(ban_for)
        ban_causes.append(reason)
        ban_names.append(by_name)
        ban_dates.append(now.strftime("%Y.%m.%d %H:%M:%S"))

        return await self.cache.edit(
            _make_cache_key(uid, chat_id),
            ban=ban_for + now.timestamp(),
            last_bans_times=f"{ban_times}",
            last_bans_causes=f"{ban_causes}",
            last_bans_names=f"{ban_names}",
            last_bans_dates=f"{ban_dates}",
        )

    async def unban(self, uid: int, chat_id: int):
        return await self.cache.edit(_make_cache_key(uid, chat_id), ensure=False, ban=0)
