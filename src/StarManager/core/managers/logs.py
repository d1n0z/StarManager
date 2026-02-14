from ast import literal_eval
from copy import deepcopy
from dataclasses import MISSING, dataclass, fields
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import Log


@dataclass
class CachedLogRow(BaseCachedModel):
    uid: int
    chat_id: int = 0
    category: int = 1
    logs: Optional[str] = None


DEFAULTS = {
    f.name: f.default
    for f in fields(CachedLogRow)
    if f.default is not MISSING and f.name not in ("uid", "chat_id", "category")
}


CacheKey: TypeAlias = Tuple[int, int, int]
Cache: TypeAlias = Dict[CacheKey, CachedLogRow]


def _make_cache_key(uid: int, chat_id: int, category: int) -> CacheKey:
    return (uid, chat_id, category)


class LogRepository(BaseRepository):
    async def ensure_record(
        self,
        uid: int,
        chat_id: int,
        category: int,
        defaults: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Log, bool]:
        obj, created = await Log.get_or_create(
            uid=uid, chat_id=chat_id, category=category, defaults=defaults
        )
        return obj, created

    async def get_record(self, uid: int, chat_id: int, category: int) -> Optional[Log]:
        return await Log.filter(uid=uid, chat_id=chat_id, category=category).first()

    async def delete_record(self, uid: int, chat_id: int, category: int):
        await Log.filter(uid=uid, chat_id=chat_id, category=category).delete()

    async def delete_chat(self, chat_id: int):
        await Log.filter(chat_id=chat_id).delete()


class LogCache(BaseCacheManager):
    MAX_LOGS_PER_CATEGORY = 20

    def __init__(self, repo: LogRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await Log.all():
                key = _make_cache_key(row.uid, row.chat_id, row.category)
                cached = CachedLogRow.from_model(row)
                self._cache[key] = cached

        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        async with self._lock:
            if cache_key in self._cache:
                return False

        uid, chat_id, category = cache_key
        model, created = await self.repo.ensure_record(
            uid,
            chat_id,
            category,
            defaults=DEFAULTS | (initial_data or {}),
        )
        cached = CachedLogRow.from_model(model)

        async with self._lock:
            self._cache[cache_key] = cached

        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedLogRow]:
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
            chat_ids = list({k[1] for k, _ in batch})
            categories = list({k[2] for k, _ in batch})

            existing = await Log.filter(
                uid__in=uids, chat_id__in=chat_ids, category__in=categories
            )
            existing_map = {
                _make_cache_key(r.uid, r.chat_id, r.category): r for r in existing
            }

            to_update, to_create = [], []
            for key, cached in batch:
                if key in existing_map:
                    row = existing_map[key]
                    dirty_flag = False
                    for field in CachedLogRow.__dataclass_fields__:
                        val = getattr(cached, field)
                        if getattr(row, field) != val:
                            setattr(row, field, val)
                            dirty_flag = True
                    if dirty_flag:
                        to_update.append(row)
                else:
                    data = cached.__dict__.copy()
                    data.update({"uid": key[0], "chat_id": key[1], "category": key[2]})
                    to_create.append(Log(**data))

            if to_update:
                update_fields = list(CachedLogRow.__dataclass_fields__.keys())
                await Log.bulk_update(
                    to_update,
                    fields=[
                        f
                        for f in update_fields
                        if f not in ("chat_id", "uid", "category")
                    ],
                    batch_size=batch_size,
                )
            if to_create:
                await Log.bulk_create(to_create, batch_size=batch_size)

        async with self._lock:
            for ck, old_val in payloads.items():
                cur = self._cache.get(ck)
                if cur is None:
                    self._dirty.discard(ck)
                    continue
                if cur.__dict__ == old_val.__dict__:
                    self._dirty.discard(ck)

    async def add_log_entry(self, cache_key: CacheKey, entry: str):
        await self._ensure_cached(cache_key, {"logs": "[]"})
        async with self._lock:
            row = self._cache[cache_key]
            logs = literal_eval(row.logs) if row.logs else []
            logs.append(entry)
            if len(logs) > self.MAX_LOGS_PER_CATEGORY:
                logs = logs[-self.MAX_LOGS_PER_CATEGORY :]
            row.logs = f"{logs}"
            self._dirty.add(cache_key)
        return True

    async def get_logs(self, cache_key: CacheKey) -> List[str]:
        async with self._lock:
            row = self._cache.get(cache_key)
            if not row or not row.logs:
                return []
            return list(literal_eval(row.logs))[::-1]


class LogManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = LogRepository()
        self.cache = LogCache(self.repo, self._cache)

    async def initialize(self):
        await self.cache.initialize()

    async def get(
        self, uid: int, chat_id: int, category: int = 1
    ) -> Optional[CachedLogRow]:
        return await self.cache.get(_make_cache_key(uid, chat_id, category))

    async def add_log(
        self,
        uid: int,
        chat_id: int,
        category: int,
        text: str,
        *,
        by_name: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        now = datetime.now()
        prefix = f"{now.strftime('%d.%m.%Y %H:%M:%S')}"
        if by_name:
            entry = f"{prefix.strip()} | {by_name.strip()} | {text.strip()}"
        else:
            entry = f"{prefix.strip()} | {text.strip()}"
        if reason:
            entry += f" | Причина: {reason.strip()}"
        return await self.cache.add_log_entry(
            _make_cache_key(uid, chat_id, category), entry
        )

    async def get_logs(self, uid: int, chat_id: int, category: int = 1) -> List[str]:
        return await self.cache.get_logs(_make_cache_key(uid, chat_id, category))

    async def clear_user_logs(self, uid: int, chat_id: int, category: int = 1):
        return await self.cache.edit(
            _make_cache_key(uid, chat_id, category), ensure=False, logs="[]"
        )
