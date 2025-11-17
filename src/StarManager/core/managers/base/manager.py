import asyncio
from abc import ABC
from typing import Any, Dict, Optional

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


class BaseEmptyManager(ABC): ...
