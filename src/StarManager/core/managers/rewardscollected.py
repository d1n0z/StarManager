from copy import deepcopy
from dataclasses import MISSING, dataclass, fields
from typing import Any, Dict, Iterable, Optional, Set, Tuple, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import RewardsCollected


@dataclass
class CachedRewardsCollectedRow(BaseCachedModel):
    uid: int
    date: int
    deactivated: bool = False


DEFAULTS = {
    f.name: f.default
    for f in fields(CachedRewardsCollectedRow)
    if f.default is not MISSING and f.name not in ("uid",)
}


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedRewardsCollectedRow]


def _make_cache_key(uid: int) -> CacheKey:
    return uid


class RewardsCollectedRepository(BaseRepository):
    async def ensure_record(
        self, uid: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[RewardsCollected, bool]:
        obj, created = await RewardsCollected.get_or_create(uid=uid, defaults=defaults)
        return obj, created

    async def get_record(self, uid: int) -> Optional[RewardsCollected]:
        return await RewardsCollected.filter(uid=uid).first()

    async def delete_record(self, uid: int):
        await RewardsCollected.filter(uid=uid).delete()

    async def delete_multiple(self, uids: Iterable[int]):
        await RewardsCollected.filter(uid__in=uids).delete()


class RewardsCollectedCache(BaseCacheManager):
    def __init__(self, repo: RewardsCollectedRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await RewardsCollected.all():
                key = _make_cache_key(row.uid)
                cached = CachedRewardsCollectedRow.from_model(row)
                self._cache[key] = cached

        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        async with self._lock:
            if cache_key in self._cache:
                return False

        uid = cache_key
        model, created = await self.repo.ensure_record(
            uid,
            defaults=DEFAULTS | (initial_data or {}),
        )
        cached = CachedRewardsCollectedRow.from_model(model)

        async with self._lock:
            self._cache[cache_key] = cached

        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedRewardsCollectedRow]:
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
            uids = list({k for k, _ in batch})

            existing = await RewardsCollected.filter(uid__in=uids)
            existing_map = {_make_cache_key(r.uid): r for r in existing}

            to_update, to_create = [], []
            for key, cached in batch:
                if key in existing_map:
                    row = existing_map[key]
                    dirty = False
                    for field in CachedRewardsCollectedRow.__dataclass_fields__:
                        val = getattr(cached, field)
                        if getattr(row, field) != val:
                            setattr(row, field, val)
                            dirty = True
                    if dirty:
                        to_update.append(row)
                else:
                    data = cached.__dict__.copy()
                    data.update({"uid": key})
                    to_create.append(RewardsCollected(**data))

            if to_update:
                update_fields = list(
                    CachedRewardsCollectedRow.__dataclass_fields__.keys()
                )
                await RewardsCollected.bulk_update(
                    to_update,
                    fields=[f for f in update_fields if f not in ("uid",)],
                    batch_size=batch_size,
                )
            if to_create:
                await RewardsCollected.bulk_create(to_create, batch_size=batch_size)

        async with self._lock:
            for ck, old_val in payloads.items():
                cur = self._cache.get(ck)
                if cur is None:
                    self._dirty.discard(ck)
                    continue
                if cur.__dict__ == old_val.__dict__:
                    self._dirty.discard(ck)

    async def get_all(self, where_deactivated: Optional[bool] = None):
        if where_deactivated is not None:
            async with self._lock:
                return [
                    i
                    for i in self._cache.values()
                    if i.deactivated == where_deactivated
                ]
        async with self._lock:
            return [i for i in self._cache.values()]


class RewardsCollectedManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo = RewardsCollectedRepository()
        self.cache = RewardsCollectedCache(self.repo, self._cache)

    async def initialize(self):
        await self.cache.initialize()

    async def get(self, uid: int) -> Optional[CachedRewardsCollectedRow]:
        return await self.cache.get(_make_cache_key(uid))

    async def turn(self, uid: int):
        u = await self.get(uid)
        return self.cache.edit(
            _make_cache_key(uid), deactivated=(not u.deactivated) if u else True
        )

    async def delete(self, uid: int):
        return await self.cache.delete(_make_cache_key(uid))

    async def get_all_activated(self):
        return await self.cache.get_all(False)
