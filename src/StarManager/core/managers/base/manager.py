import asyncio
from abc import ABC
from typing import Any, Dict, List, Optional

from StarManager.core.managers.base.cache import BaseCacheManager
from StarManager.core.managers.base.repository import BaseRepository


class BaseManager(ABC):
    def __init__(
        self,
        repo: Optional[BaseRepository] = None,
        cache: Optional[BaseCacheManager] = None,
    ):
        self._lock = asyncio.Lock()
        self._cache: Dict[Any, Any] = {}
        self.repo = repo
        self.cache = cache
    
    async def initialize(self):
        if self.cache is not None:
            await self.cache.initialize()

    async def close(self):
        if self.cache is not None:
            await self.cache.close()

    async def sync(self):
        if self.cache is not None:
            await self.cache.sync()


class BaseManagerGroup(ABC):
    def __init__(self):
        self.managers: List[BaseManager] = []
    
    async def initialize(self):
        for m in self.managers:
            if m.cache is not None:
                await m.cache.initialize()

    async def close(self):
        for m in self.managers:
            if m.cache is not None:
                await m.cache.sync()
                await m.cache.close()

    async def sync(self):
        for m in self.managers:
            if m.cache is not None:
                await m.cache.sync()


class BaseEmptyManager(ABC): ...
