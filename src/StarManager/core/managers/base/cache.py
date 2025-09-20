import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Set


class BaseCacheManager(ABC):
    def __init__(self, sync_interval: int = 10):
        self._cache: Dict[Any, Any] = {}
        self._dirty: Set[Any] = set()
        self._lock = asyncio.Lock()
        self._sync_interval = sync_interval
        self._sync_task = None
    
    @abstractmethod
    async def initialize(self):
        """Must call super().initialize()"""
        self._start_sync_task()

    def _start_sync_task(self):
        if not self._sync_task:
            self._sync_task = asyncio.create_task(self._sync_loop())

    async def _sync_loop(self):
        while True:
            await asyncio.sleep(self._sync_interval)
            await self.sync()

    @abstractmethod
    async def sync(self):
        pass

    async def close(self):
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        await self.sync()
