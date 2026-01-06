from ast import literal_eval
from copy import deepcopy
from dataclasses import MISSING, dataclass, fields
from typing import Any, Dict, Optional, Set, Tuple, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import SilenceMode


@dataclass
class CachedSilenceModeRow(BaseCachedModel):
    chat_id: int
    activated: bool = False
    allowed: str = "[]"
    allowed_custom: str = "[]"


DEFAULTS = {
    f.name: f.default
    for f in fields(CachedSilenceModeRow)
    if f.default is not MISSING and f.name not in ("chat_id",)
}


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedSilenceModeRow]


def _make_cache_key(chat_id: int) -> CacheKey:
    return chat_id


class SilenceModeRepository(BaseRepository):
    async def ensure_record(
        self, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[SilenceMode, bool]:
        obj, created = await SilenceMode.get_or_create(
            chat_id=chat_id, defaults=defaults
        )
        return obj, created

    async def get_record(self, chat_id: int) -> Optional[SilenceMode]:
        return await SilenceMode.filter(chat_id=chat_id).first()

    async def delete_record(self, chat_id: int):
        await SilenceMode.filter(chat_id=chat_id).delete()


class SilenceModeCache(BaseCacheManager):
    def __init__(self, repo: SilenceModeRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await SilenceMode.all():
                key = _make_cache_key(row.chat_id)
                cached = CachedSilenceModeRow.from_model(row)
                self._cache[key] = cached

        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        async with self._lock:
            if cache_key in self._cache:
                return False

        chat_id = cache_key
        model, created = await self.repo.ensure_record(
            chat_id,
            defaults=DEFAULTS | (initial_data or {}),
        )
        cached = CachedSilenceModeRow.from_model(model)

        async with self._lock:
            self._cache[cache_key] = cached

        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedSilenceModeRow]:
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

    async def turn(self, cache_key: CacheKey):
        await self._ensure_cached(cache_key)
        async with self._lock:
            new_value = not self._cache[cache_key].activated
            self._cache[cache_key].activated = new_value
            self._dirty.add(cache_key)
        return new_value

    async def turn_lvl(self, cache_key: CacheKey, level: int, is_custom: bool):
        await self._ensure_cached(cache_key)
        async with self._lock:
            attr = "allowed"
            if is_custom:
                attr += "_custom"
            value: list = literal_eval(getattr(self._cache[cache_key], attr))
            if level in value:
                value.remove(level)
            else:
                value.append(level)
            setattr(self._cache[cache_key], attr, f"{value}")
            self._dirty.add(cache_key)
        return value

    async def delete(self, cache_key: CacheKey):
        async with self._lock:
            if cache_key not in self._cache:
                return
            del self._cache[cache_key]
            self._dirty.discard(cache_key)
        try:
            await self.repo.delete_record(cache_key)
        except Exception:
            pass

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
            chat_ids = list({k for k, _ in batch})

            existing = await SilenceMode.filter(chat_id__in=chat_ids)
            existing_map = {_make_cache_key(r.chat_id): r for r in existing}

            to_update, to_create = [], []
            for key, cached in batch:
                if key in existing_map:
                    row = existing_map[key]
                    dirty = False
                    for field in CachedSilenceModeRow.__dataclass_fields__:
                        val = getattr(cached, field)
                        if getattr(row, field) != val:
                            setattr(row, field, val)
                            dirty = True
                    if dirty:
                        to_update.append(row)
                else:
                    data = cached.__dict__.copy()
                    data.update({"chat_id": key})
                    to_create.append(SilenceMode(**data))

            if to_update:
                update_fields = list(CachedSilenceModeRow.__dataclass_fields__.keys())
                await SilenceMode.bulk_update(
                    to_update,
                    fields=[f for f in update_fields if f not in ("chat_id",)],
                    batch_size=batch_size,
                )
            if to_create:
                await SilenceMode.bulk_create(to_create, batch_size=batch_size)

        async with self._lock:
            for ck, old_val in payloads.items():
                cur = self._cache.get(ck)
                if cur is None:
                    self._dirty.discard(ck)
                    continue
                if cur.__dict__ == old_val.__dict__:
                    self._dirty.discard(ck)


class SilenceModeManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = SilenceModeRepository()
        self.cache = SilenceModeCache(self.repo, self._cache)
        
        self.edit = self.cache.edit

    async def initialize(self):
        await self.cache.initialize()

    async def get(self, chat_id: int) -> Optional[CachedSilenceModeRow]:
        return await self.cache.get(_make_cache_key(chat_id))

    async def turn(self, chat_id: int):
        return await self.cache.turn(_make_cache_key(chat_id))

    async def turn_lvl(self, chat_id: int, lvl: int, custom: bool):
        return await self.cache.turn_lvl(_make_cache_key(chat_id), lvl, custom)

    async def delete(self, chat_id: int):
        return await self.cache.delete(_make_cache_key(chat_id))
