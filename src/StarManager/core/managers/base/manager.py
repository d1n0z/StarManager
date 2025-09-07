import asyncio
from abc import ABC
from typing import Any, Dict, List, Optional

from StarManager.core.managers.base.cache import BaseCacheManager
from StarManager.core.managers.base.repository import BaseRepository


class BaseManager(ABC):
    def __init__(self, repo: Optional[BaseRepository] = None, cache: Optional[BaseCacheManager] = None):
        self._lock = asyncio.Lock()
        self._items: List[Any] = []
        self._cache: Dict[Any, Any] = {}
        self.repo = repo
        self.cache = cache

    async def close(self):
        if self.cache is not None:
            await self.cache.close()


class BaseEmptyManager(ABC):
    ...
