from dataclasses import dataclass
from typing import Dict, Set, TypeAlias

from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
)
from StarManager.core.tables import CommandNames


@dataclass
class CachedCommandNamesRow(BaseCachedModel):
    uid: int
    cmds: Dict[str, str]


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedCommandNamesRow]


class CommandNamesCache(BaseCacheManager):
    def __init__(self, cache: Cache):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()

    async def initialize(self):
        async with self._lock:
            self._cache.clear()
            self._dirty.clear()

            for row in await CommandNames.all():
                key = row.uid
                if key not in self._cache:
                    self._cache[key] = CachedCommandNamesRow(uid=row.uid, cmds={})
                self._cache[key].cmds[row.cmd] = row.name

        await super().initialize()

    async def sync(self, batch_size: int = 200):
        async with self._lock:
            if not self._dirty:
                return
            dirty = set(self._dirty)
            payloads = {k: dict(self._cache[k].cmds) for k in dirty if k in self._cache}

        if not payloads:
            async with self._lock:
                self._dirty.difference_update(dirty)
            return

        items = list(payloads.items())
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            uids = [uid for uid, _ in batch]

            existing_rows = await CommandNames.filter(uid__in=uids)
            existing_map: Dict[int, Dict[str, str]] = {}
            for r in existing_rows:
                existing_map.setdefault(r.uid, {})[r.cmd] = r.name

            to_create = []
            to_update = []
            to_delete_by_uid = {}

            for uid, cached_cmds in batch:
                db_cmds = existing_map.get(uid, {})

                for cmd, name in cached_cmds.items():
                    if cmd not in db_cmds:
                        to_create.append(CommandNames(uid=uid, cmd=cmd, name=name))
                    else:
                        if db_cmds[cmd] != name:
                            to_update.append((uid, cmd, name))

                delete_cmds = set(db_cmds.keys()) - set(cached_cmds.keys())
                if delete_cmds:
                    to_delete_by_uid[uid] = delete_cmds

            if to_create:
                await CommandNames.bulk_create(
                    to_create, ignore_conflicts=True, batch_size=batch_size
                )
            for uid, cmd, new_name in to_update:
                await CommandNames.filter(uid=uid, cmd=cmd).update(name=new_name)

            for uid, del_cmds in to_delete_by_uid.items():
                await CommandNames.filter(uid=uid, cmd__in=list(del_cmds)).delete()

        async with self._lock:
            self._dirty.difference_update(dirty)

    async def new_cmd(self, key: CacheKey, cmd: str, name: str):
        uid = key
        async with self._lock:
            if key not in self._cache:
                self._cache[key] = CachedCommandNamesRow(uid=uid, cmds={})
            current = self._cache[key].cmds.get(cmd)
            if current == name:
                return False
            self._cache[key].cmds[cmd] = name
            self._dirty.add(key)
        return True

    async def del_cmd(self, key: CacheKey, cmd: str):
        async with self._lock:
            if key not in self._cache or cmd not in self._cache[key].cmds:
                return None
            obj = self._cache[key].cmds[cmd]
            del self._cache[key].cmds[cmd]
            self._dirty.add(key)
        return obj

    async def edit_cmd(self, key: CacheKey, cmd: str, new_name: str) -> bool:
        async with self._lock:
            if key not in self._cache or cmd not in self._cache[key].cmds:
                return False
            if self._cache[key].cmds[cmd] == new_name:
                return False
            self._cache[key].cmds[cmd] = new_name
            self._dirty.add(key)
        return True

    async def get_or_none(self, key: CacheKey, cmd_or_name: str):
        async with self._lock:
            if key in self._cache:
                for cmd, name in self._cache[key].cmds.items():
                    if cmd_or_name == name or cmd_or_name == cmd:
                        return cmd
            return None

    async def get_all_cmds(self, key: CacheKey) -> Dict[str, str]:
        async with self._lock:
            if key in self._cache:
                return dict(self._cache[key].cmds)
            return {}

    async def del_all_cmds(self, key: CacheKey):
        async with self._lock:
            if key not in self._cache:
                return False
            if not self._cache[key].cmds:
                return False
            self._cache[key].cmds.clear()
            self._dirty.add(key)
        return True


class CommandNamesManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.cache = CommandNamesCache(self._cache)

    async def get_or_none(self, uid: int, cmd_or_name: str):
        return await self.cache.get_or_none(uid, cmd_or_name)

    async def new_cmd(self, uid: int, cmd: str, name: str):
        return await self.cache.new_cmd(uid, cmd, name)

    async def del_cmd(self, uid: int, cmd: str):
        return await self.cache.del_cmd(uid, cmd)

    async def edit_cmd(self, uid: int, cmd: str, new_name: str):
        return await self.cache.edit_cmd(uid, cmd, new_name)

    async def del_all(self, uid: int):
        return await self.cache.del_all_cmds(uid)

    async def get_all(self, uid: int) -> Dict[str, str]:
        return await self.cache.get_all_cmds(uid)
