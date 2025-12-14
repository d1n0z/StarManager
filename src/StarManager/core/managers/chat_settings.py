import copy
from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeAlias,
    Union,
    overload,
)

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import Settings as ChatSettings

DEFAULTS = {
    "pos": None,
    "pos2": None,
    "value": None,
    "value2": None,
    "punishment": None,
}


@dataclass
class CachedChatSettingsRow(BaseCachedModel):
    id: int
    pos: Optional[bool] = None
    pos2: Optional[bool] = None
    value: Optional[int] = None
    value2: Optional[str] = None
    punishment: Optional[str] = None


CacheKey: TypeAlias = Tuple[int, str]
Cache: TypeAlias = Dict[CacheKey, CachedChatSettingsRow]


def _make_cache_key(chat_id: int, setting: str) -> CacheKey:
    return chat_id, setting


class ChatSettingsRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def ensure_record(
        self, chat_id: int, setting: str, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[ChatSettings, bool]:
        defaults = defaults or {}
        obj, created = await ChatSettings.get_or_create(
            chat_id=chat_id,
            setting=setting,
            defaults=(
                defaults | {k: v for k, v in DEFAULTS.items() if k not in defaults}
            ),
        )
        return obj, created

    async def get_record(self, chat_id: int, setting: str) -> Optional[ChatSettings]:
        return await ChatSettings.filter(chat_id=chat_id, setting=setting).first()

    async def delete_record(self, chat_id: int, setting: str):
        await ChatSettings.filter(chat_id=chat_id, setting=setting).delete()


class ChatSettingsCache(BaseCacheManager):
    def __init__(
        self,
        repo: ChatSettingsRepository,
        cache: Cache,
    ):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        rows = await ChatSettings.all()
        async with self._lock:
            for row in rows:
                key = _make_cache_key(row.chat_id, row.setting)
                self._cache[key] = CachedChatSettingsRow.from_model(row)

        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ):
        async with self._lock:
            if cache_key in self._cache:
                return False

        defaults = initial_data or DEFAULTS
        model, created = await self.repo.ensure_record(*cache_key, defaults=defaults)
        async with self._lock:
            self._cache[cache_key] = CachedChatSettingsRow.from_model(model)
        return created

    async def get_by_id(self, id: int) -> CacheKey:
        async with self._lock:
            return next((k for k, v in self._cache.items() if v.id == id))

    async def get_by_field(self, **fields):
        async with self._lock:
            return tuple(
                [
                    k
                    for k, r in self._cache.items()
                    if all(
                        (  # get from key(chat_id, setting) or from model
                            (k[f == "setting"] == v)
                            if f in ("chat_id", "setting")
                            else (getattr(r, f, None) == v)
                            # every field is None by default, so getattr with None as default is not a problem (i hope so...)
                        )
                        for f, v in fields.items()
                    )
                ]
            )

    @overload
    async def get(self, chat_id: int, setting: str, fields: str) -> Any: ...

    @overload
    async def get(
        self, chat_id: int, setting: str, fields: Sequence[str]
    ) -> Tuple[Any, ...]: ...

    async def get(self, chat_id: int, setting: str, fields: Union[str, Sequence[str]]):
        cache_key = _make_cache_key(chat_id, setting)
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

    async def edit(self, chat_id: int, setting: str, **fields):
        cache_key = _make_cache_key(chat_id, setting)
        await self._ensure_cached(cache_key, initial_data=fields)
        async with self._lock:
            for field, value in fields.items():
                if hasattr(self._cache[cache_key], field):
                    setattr(self._cache[cache_key], field, value)
            self._dirty.add(cache_key)

    async def remove(self, chat_id: int, setting: Optional[str] = None):
        if setting:
            cache_key = _make_cache_key(chat_id, setting)
            async with self._lock:
                if cache_key in self._cache:
                    self._dirty.discard(cache_key)
                    del self._cache[cache_key]
            await self.repo.delete_record(*cache_key)
            return
        
        async with self._lock:
            keys = [k for k in self._cache.keys() if k[0] == chat_id]
            for cache_key in keys:
                self._dirty.discard(cache_key)
                del self._cache[cache_key]
        for cache_key in keys:
            await self.repo.delete_record(*cache_key)

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty_snapshot = set(self._dirty)
            payloads = {
                cache_key: copy.deepcopy(self._cache[cache_key])
                for cache_key in dirty_snapshot
                if cache_key in self._cache
            }

        if not payloads:
            return

        items = list(payloads.items())
        try:
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                chat_ids = list({ck[0] for ck, _ in batch})
                existing_rows = await ChatSettings.filter(chat_id__in=chat_ids)
                existing_map = {
                    (row.chat_id, getattr(row, "setting")): row for row in existing_rows
                }

                to_update, to_create = [], []
                for cache_key, cached in batch:
                    if cache_key in existing_map:
                        row = existing_map[cache_key]
                        dirty = False
                        for field in CachedChatSettingsRow.__dataclass_fields__:
                            val = getattr(cached, field)
                            if getattr(row, field) != val:
                                setattr(row, field, val)
                                dirty = True
                        if dirty:
                            to_update.append(row)
                    else:
                        data = cached.__dict__.copy()
                        data.update({"chat_id": cache_key[0], "setting": cache_key[1]})
                        to_create.append(ChatSettings(**data))

                if to_update:
                    update_fields = list(
                        CachedChatSettingsRow.__dataclass_fields__.keys()
                    )
                    update_fields = [
                        f for f in update_fields if f not in ("chat_id", "setting")
                    ]
                    if update_fields and to_update:
                        await ChatSettings.bulk_update(
                            to_update, fields=update_fields, batch_size=batch_size
                        )

                if to_create:
                    await ChatSettings.bulk_create(to_create, batch_size=batch_size)

        except Exception:
            from loguru import logger

            logger.exception("ChatSettings sync failed")
            return

        async with self._lock:
            for ck, old_val in payloads.items():
                cur = self._cache.get(ck)
                if cur is None:
                    self._dirty.discard(ck)
                    continue
                if cur.__dict__ == old_val.__dict__:
                    self._dirty.discard(ck)


class ChatSettingsManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache
        self.repo: ChatSettingsRepository = ChatSettingsRepository()
        self.cache: ChatSettingsCache = ChatSettingsCache(self.repo, self._cache)

        self.get = self.cache.get
        self.get_by_id = self.cache.get_by_id
        self.get_by_field = self.cache.get_by_field
        self.edit = self.cache.edit
        self.remove = self.cache.remove

    async def initialize(self):
        await self.cache.initialize()
