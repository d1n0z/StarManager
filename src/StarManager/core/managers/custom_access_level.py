from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import CustomAccessLevel


@dataclass
class CachedCustomAccessLevelRow(BaseCachedModel):
    id: int
    chat_id: int
    access_level: int
    name: str
    emoji: Optional[str] = None
    status: bool = False
    commands: List[str] = list  # type: ignore


CacheKey: TypeAlias = Tuple[int, int]
Cache: TypeAlias = Dict[CacheKey, CachedCustomAccessLevelRow]


def _make_cache_key(access_level: int, chat_id: int) -> CacheKey:
    return access_level, chat_id


class CustomAccessLevelRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def ensure_record(
        self, access_level: int, chat_id: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[CustomAccessLevel, bool]:
        obj, created = await CustomAccessLevel.get_or_create(
            access_level=access_level, chat_id=chat_id, defaults=defaults
        )
        return obj, created

    async def get_record(
        self, access_level: int, chat_id: int
    ) -> Optional[CustomAccessLevel]:
        return await CustomAccessLevel.filter(
            access_level=access_level, chat_id=chat_id
        ).first()

    async def delete_record(self, access_level: int, chat_id: int):
        await CustomAccessLevel.filter(
            access_level=access_level, chat_id=chat_id
        ).delete()


class CustomAccessLevelCache(BaseCacheManager):
    def __init__(self, repo: CustomAccessLevelRepository, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.repo = repo

    async def initialize(self):
        async with self._lock:
            for row in await CustomAccessLevel.all():
                key = _make_cache_key(row.access_level, row.chat_id)
                self._cache[key] = CachedCustomAccessLevelRow.from_model(row)
        await super().initialize()

    async def _ensure_cached(
        self, cache_key: CacheKey, initial_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        async with self._lock:
            if cache_key in self._cache:
                return False

        access_level, chat_id = cache_key
        model, created = await self.repo.ensure_record(
            access_level, chat_id, defaults=initial_data
        )
        async with self._lock:
            self._cache[cache_key] = CachedCustomAccessLevelRow.from_model(model)
        return created

    async def get(self, cache_key: CacheKey) -> Optional[CachedCustomAccessLevelRow]:
        async with self._lock:
            obj = self._cache.get(cache_key)
            return deepcopy(obj)

    async def edit(self, cache_key: CacheKey, **fields) -> CachedCustomAccessLevelRow:
        await self._ensure_cached(cache_key, fields)
        async with self._lock:
            if cache_key in self._cache:
                for k, v in fields.items():
                    if k == "commands":
                        if v is None:
                            setattr(self._cache[cache_key], k, [])
                        else:
                            setattr(self._cache[cache_key], k, list(v))
                    else:
                        setattr(self._cache[cache_key], k, v)
            self._dirty.add(cache_key)
            return self._cache[cache_key]

    async def edit_access_level(
        self, cache_key: CacheKey, new_access_level: int, **initial_data
    ) -> None:
        created = await self._ensure_cached(cache_key, initial_data)
        new_cache_key = _make_cache_key(new_access_level, cache_key[1])
        async with self._lock:
            if not created:
                self._dirty.discard(cache_key)
                obj = self._cache[cache_key]
                obj.access_level = new_access_level
                self._cache[new_cache_key] = obj
                del self._cache[cache_key]
            else:
                if new_cache_key in self._cache:
                    self._cache[new_cache_key].access_level = new_access_level
            self._dirty.add(new_cache_key)
        await self.repo.delete_record(*cache_key)

    async def remove(self, cache_key: CacheKey) -> Optional[CachedCustomAccessLevelRow]:
        removed_item = None
        async with self._lock:
            if cache_key in self._cache:
                removed_item = deepcopy(self._cache[cache_key])
                self._dirty.discard(cache_key)
                del self._cache[cache_key]

        if removed_item is not None:
            await self.repo.delete_record(*cache_key)

        return removed_item

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty_snapshot = set(self._dirty)
            payloads = {
                key: {
                    "name": self._cache[key].name,
                    "emoji": self._cache[key].emoji,
                    "status": self._cache[key].status,
                    "commands": list(self._cache[key].commands),
                }
                for key in dirty_snapshot
                if key in self._cache
            }

        if not payloads:
            return

        items = list(payloads.items())

        try:
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                access_levels = list({key[0] for key, _ in batch})
                chat_ids = list({key[1] for key, _ in batch})

                existing_rows = await CustomAccessLevel.filter(
                    access_level__in=access_levels, chat_id__in=chat_ids
                )

                keys_set = {k for k, _ in batch}
                existing_map = {
                    _make_cache_key(row.access_level, row.chat_id): row
                    for row in existing_rows
                    if _make_cache_key(row.access_level, row.chat_id) in keys_set
                }

                to_update, to_create = [], []
                for key, data in batch:
                    if key in existing_map:
                        row = existing_map[key]
                        changed = False

                        if row.name != data["name"]:
                            row.name = data["name"]
                            changed = True
                        if getattr(row, "emoji", None) != data["emoji"]:
                            row.emoji = data["emoji"]
                            changed = True
                        if getattr(row, "status", False) != data["status"]:
                            row.status = data["status"]
                            changed = True
                        existing_cmds = getattr(row, "commands", None) or []
                        if list(existing_cmds) != list(data["commands"]):
                            row.commands = list(data["commands"])
                            changed = True

                        if changed:
                            to_update.append(row)
                    else:
                        access_level, chat_id = key
                        to_create.append(
                            CustomAccessLevel(
                                access_level=access_level,
                                chat_id=chat_id,
                                name=data["name"],
                                emoji=data.get("emoji"),
                                status=data.get("status", False),
                                commands=data.get("commands", []),
                            )
                        )

                if to_update:
                    await CustomAccessLevel.bulk_update(
                        to_update,
                        fields=["name", "emoji", "status", "commands"],
                        batch_size=batch_size,
                    )
                if to_create:
                    await CustomAccessLevel.bulk_create(
                        to_create, batch_size=batch_size
                    )
        except Exception:
            from loguru import logger

            logger.exception("CustomAccessLevel sync failed")
            return

        async with self._lock:
            for key, old_payload in payloads.items():
                cur = self._cache.get(key)
                if cur is None:
                    self._dirty.discard(key)
                    continue
                if (
                    cur.name == old_payload["name"]
                    and cur.emoji == old_payload["emoji"]
                    and cur.status == old_payload["status"]
                    and list(cur.commands) == list(old_payload["commands"])
                ):
                    self._dirty.discard(key)

    async def get_all(
        self,
        chat_id: Optional[int] = None,
        *,
        predicate: Optional[Callable[[CachedCustomAccessLevelRow], Any]] = None,
    ) -> List[CachedCustomAccessLevelRow]:
        predicate = predicate or (lambda i: i.access_level > 0)

        def predicate_chat_id(i: CachedCustomAccessLevelRow):
            if chat_id is None:
                return True
            return i.chat_id == chat_id

        def pred(i: CachedCustomAccessLevelRow):
            return predicate(i) and predicate_chat_id(i)

        async with self._lock:
            snapshot = list(self._cache.values())
        return [deepcopy(i) for i in snapshot if pred(i)]

    async def get_by_name(self, name: str, chat_id: int):
        async with self._lock:
            for row in self._cache.values():
                if row.chat_id == chat_id and row.name == name:
                    return deepcopy(row)

    async def turn_commands(self, cache_key: CacheKey, commands: Iterable[str]) -> None:
        await self._ensure_cached(cache_key)
        async with self._lock:
            row = self._cache.get(cache_key)
            if row is None:
                return
            cmds = list(row.commands) if row.commands else []
            for command in commands:
                if command in cmds:
                    cmds.remove(command)
                else:
                    cmds.append(command)
            row.commands = cmds
            self._dirty.add(cache_key)

    async def set_preset(self, cache_key: CacheKey, commands: Iterable[str]) -> None:
        await self._ensure_cached(cache_key)
        async with self._lock:
            row = self._cache.get(cache_key)
            if row is None:
                return
            row.commands.clear()
            row.commands.extend(commands)
            self._dirty.add(cache_key)


class CustomAccessLevelManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.repo: CustomAccessLevelRepository = CustomAccessLevelRepository()
        self.cache: CustomAccessLevelCache = CustomAccessLevelCache(
            self.repo, self._cache
        )

        self.get_by_name = self.cache.get_by_name
        self.get_all = self.cache.get_all

    async def initialize(self):
        await self.cache.initialize()

    async def get(self, access_level: int, chat_id: int):
        return await self.cache.get(_make_cache_key(access_level, chat_id))

    async def is_active(self, access_level: int, chat_id: int):
        lvl = await self.cache.get(_make_cache_key(access_level, chat_id))
        return lvl.status if lvl else True

    async def turn_commands(self, access_level: int, chat_id: int, commands: Iterable[str]):
        return await self.cache.turn_commands(_make_cache_key(access_level, chat_id), commands)

    async def set_preset(self, access_level: int, chat_id: int, commands: Iterable[str]):
        return await self.cache.set_preset(_make_cache_key(access_level, chat_id), commands)

    async def edit(
        self, access_level: int, chat_id: int, **fields
    ) -> CachedCustomAccessLevelRow:
        return await self.cache.edit(_make_cache_key(access_level, chat_id), **fields)

    async def edit_access_level(
        self,
        access_level: int,
        chat_id: int,
        new_access_level: int,
        **initial_data
    ) -> Optional[CachedCustomAccessLevelRow]:
        if new_access_level == 0:
            return await self.delete(access_level, chat_id)
        await self.cache.edit_access_level(
            _make_cache_key(access_level, chat_id),
            new_access_level=new_access_level,
            **initial_data,
        )

    async def delete(
        self, access_level: int, chat_id: int
    ) -> Optional[CachedCustomAccessLevelRow]:
        return await self.cache.remove(_make_cache_key(access_level, chat_id))
