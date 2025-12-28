import copy
import time
from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeAlias,
    Union,
    overload,
)

from StarManager.core.config import api, settings
from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import XP

DEFAULTS = {
    "xp": 0.0,
    "coins": 0,
    "coins_limit": 0,
    "lvl": 1,
    "league": 1,
    "lm": 0,
    "lvm": 0,
    "lsm": 0,
}


@dataclass
class CachedXPRow(BaseCachedModel):
    xp: float
    coins: int
    coins_limit: int
    lvl: int
    league: int
    lm: int
    lvm: int
    lsm: int


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedXPRow]


def _make_cache_key(uid: int) -> CacheKey:
    return uid


class XPRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def ensure_record(
        self, uid: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[XP, bool]:
        defaults = defaults or {}
        obj, created = await XP.get_or_create(
            uid=uid,
            defaults=defaults,
        )
        return obj, created

    async def get_record(self, uid: int) -> Optional[XP]:
        return await XP.filter(uid=uid).first()

    async def delete_record(self, uid: int):
        await XP.filter(uid=uid).delete()

    async def nullify_xp_limit(self):
        await XP.filter(coins_limit__gt=0).update(coins_limit=0)


class XPCache(BaseCacheManager):
    def __init__(
        self,
        repo: XPRepository,
        cache: Cache,
    ):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey]
        self.repo = repo

    async def initialize(self):
        rows = await XP.all()
        async with self._lock:
            for row in rows:
                key = _make_cache_key(row.uid)
                self._cache[key] = CachedXPRow.from_model(row)

        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ):
        async with self._lock:
            if cache_key in self._cache:
                return False

        uid = cache_key
        if initial_data:
            defaults = initial_data | {k: v for k, v in DEFAULTS.items() if k not in initial_data or initial_data[k] is None}
        else:
            defaults = copy.deepcopy(DEFAULTS)
        model, created = await self.repo.ensure_record(uid, defaults=defaults)
        async with self._lock:
            self._cache[cache_key] = CachedXPRow.from_model(model)
        return created

    @overload
    async def get(self, cache_key: CacheKey, fields: str) -> Any: ...

    @overload
    async def get(
        self, cache_key: CacheKey, fields: Sequence[str]
    ) -> Tuple[Any, ...]: ...

    async def get(self, cache_key: CacheKey, fields: Union[str, Sequence[str]]):
        async with self._lock:
            obj = self._cache.get(cache_key)

        if isinstance(fields, str):
            if obj is None:
                return None
            return getattr(obj, fields, None)
        else:
            if obj is None:
                return tuple([None for _ in fields])
            return tuple([getattr(obj, f, None) for f in fields])

    async def edit(self, cache_key: CacheKey, **fields):
        await self._ensure_cached(cache_key, initial_data=fields)
        async with self._lock:
            for field, value in fields.items():
                if hasattr(self._cache[cache_key], field):
                    setattr(self._cache[cache_key], field, value)
            self._dirty.add(cache_key)

    async def remove(self, cache_key: CacheKey):
        async with self._lock:
            if cache_key in self._cache:
                self._dirty.discard(cache_key)
                del self._cache[cache_key]
        uid = cache_key
        await self.repo.delete_record(uid)

    async def sync_from_db(self):
        rows = await XP.all()

        new_cache: Cache = {}
        for row in rows:
            key = _make_cache_key(row.uid)
            new_cache[key] = CachedXPRow.from_model(row)

        async with self._lock:
            dirty_snapshot = set(self._dirty)

            for uid in dirty_snapshot:
                cur = self._cache.get(uid)
                if cur is not None:
                    new_cache[uid] = copy.deepcopy(cur)

            self._cache.clear()
            self._cache.update(new_cache)

    async def nullify_xp_limit(self):
        await self.repo.nullify_xp_limit()
        async with self._lock:
            for obj in self._cache.values():
                obj.coins_limit = 0

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty_snapshot = set(self._dirty)
            payloads = {
                uid: copy.deepcopy(self._cache[uid])
                for uid in dirty_snapshot
                if uid in self._cache
            }

        if not payloads:
            return

        items = list(payloads.items())
        try:
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                uids = [uid for uid, _ in batch]

                existing_rows = await XP.filter(uid__in=uids)
                existing_map = {row.uid: row for row in existing_rows}

                to_update, to_create = [], []
                for uid, cached in batch:
                    if uid in existing_map:
                        row = existing_map[uid]
                        dirty = False
                        for field in CachedXPRow.__dataclass_fields__:
                            val = getattr(cached, field)
                            if getattr(row, field) != val:
                                setattr(row, field, val)
                                dirty = True
                        if dirty:
                            to_update.append(row)
                    else:
                        to_create.append(XP(uid=uid, **cached.__dict__))

                if to_update:
                    await XP.bulk_update(
                        to_update,
                        fields=list(CachedXPRow.__dataclass_fields__.keys()),
                        batch_size=batch_size,
                    )
                if to_create:
                    await XP.bulk_create(to_create, batch_size=batch_size)
        except Exception:
            from loguru import logger

            logger.exception("XP sync failed")
            return

        async with self._lock:
            for uid, old_val in payloads.items():
                cur = self._cache.get(uid)
                if cur is None:
                    self._dirty.discard(uid)
                    continue
                if cur.__dict__ == old_val.__dict__:
                    self._dirty.discard(uid)


class XPManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache
        self.repo: XPRepository = XPRepository()
        self.cache: XPCache = XPCache(self.repo, self._cache)

        self.get = self.cache.get
        self.edit = self.cache.edit
        self.remove = self.cache.remove
        self.nullify_xp_limit = self.cache.nullify_xp_limit

    async def initialize(self):
        await self.cache.initialize()

    async def get_xp_top(
        self, league: int, uids: List[int] | None, limit: int = 10
    ) -> List[tuple[CacheKey, CachedXPRow]]:
        async with self._lock:
            top = [
                (uid, obj)
                for uid, obj in self.cache._cache.items()
                if (uids is None or uid in uids) and uid > 0 and obj.league == league
            ]
        top = sorted(top, key=lambda x: (-x[1].lvl, -x[1].xp))[:limit]
        return [(uid, copy.deepcopy(obj)) for uid, obj in top]

    async def get_coins_top(self, in_uids: List[int] | None = None, limit: int = 10):
        async with self._lock:
            top = sorted(
                self.cache._cache.items(),
                key=lambda i: i[1].coins,
                reverse=True,
            )
        top = [
            (uid, obj)
            for uid, obj in top
            if uid > 0 and (in_uids is None or uid in in_uids)
        ][:100]
        if not top:
            return []
        uids = {
            u.id: u
            for u in await api.users.get(
                user_ids=[i[0] for i in top],
                fields=["deactivated"],  # type: ignore
            )
        }
        return [
            (uid, copy.deepcopy(i))
            for uid, i in top
            if uids is None or (uid in uids and not uids[uid].deactivated)
        ][:limit]

    async def add_user_xp(self, uid: int, addxp: float):
        """returns True on level up"""
        uxp, oldlvl, ulg = await self.cache.get(uid, ["xp", "lvl", "league"])
        if uxp is None:
            return await self.cache.edit(
                uid,
                xp=addxp,
                lm=int(time.time()),
                lvm=int(time.time()),
                lsm=int(time.time()),
            )

        uxp += addxp
        ulvl = oldlvl + int(uxp // 1000)
        uxp %= 1000
        if (
            ulg != len(settings.leagues.required_level)
            and ulvl >= settings.leagues.required_level[ulg]
        ):
            await self.cache.edit(uid, xp=0.0, league=ulg + 1, lvl=1)
        else:
            await self.cache.edit(uid, xp=uxp, lvl=ulvl)
        return oldlvl != ulvl

    async def add_user_coins(
        self, uid: int, addcoins: int, u_limit: int, addlimit: bool
    ):
        coins, coins_limit = await self.cache.get(uid, ["coins", "coins_limit"])
        if coins is None:
            return await self.cache.edit(
                uid,
                coins=coins,
                coins_limit=addcoins if addlimit else 0,
                lm=int(time.time()),
                lvm=int(time.time()),
                lsm=int(time.time()),
            )
        if addlimit and coins_limit > u_limit:
            return

        bonus_coins = 100 if addlimit and (coins_limit + addcoins > u_limit) else 0
        await self.cache.edit(
            uid,
            coins=coins + addcoins + bonus_coins,
            coins_limit=coins_limit + (addcoins if addlimit else 0),
        )
        if bonus_coins == 100:
            return "bonus"

    async def get_not_empty_leagues(self):
        async with self._lock:
            leagues = set()
            for obj in self.cache._cache.values():
                leagues.add(obj.league)
        return leagues

    async def delete(self, uid: int):
        await self.cache.remove(_make_cache_key(uid))
