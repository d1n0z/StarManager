import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Set


class BaseCacheManager(ABC):
    def __init__(self, sync_interval: int = 30, reload_interval: int = 30):
        self._cache: Dict[Any, Any] = {}
        self._dirty: Set[Any] = set()
        self._lock = asyncio.Lock()

        self._sync_interval = float(sync_interval)
        self._reload_interval = float(reload_interval)

        self._sync_task: Optional[asyncio.Task] = None
        self._reload_task: Optional[asyncio.Task] = None
        self._stopping = False

    @abstractmethod
    async def initialize(self):
        """Must call super().initialize() or self._start_tasks()"""
        self._start_tasks()

    def _start_tasks(self):
        if self._sync_task is None:
            self._sync_task = asyncio.create_task(
                self._task_loop(self._sync_interval, self.sync),
                name=f"{self.__class__.__name__}-sync",
            )

        if self._should_run_reload():
            self._reload_task = asyncio.create_task(
                self._task_loop(self._reload_interval, self.reload_from_db),
                name=f"{self.__class__.__name__}-reload",
            )

    def _should_run_reload(self) -> bool:
        base_method = BaseCacheManager.reload_from_db
        subclass_method = getattr(self, "reload_from_db", None)
        return subclass_method is not None and subclass_method is not base_method

    async def _task_loop(self, interval_seconds: float, coro):
        await asyncio.sleep(0.1)
        while not self._stopping:
            await asyncio.sleep(interval_seconds)
            await coro()

    @abstractmethod
    async def sync(self):
        pass

    async def reload_from_db(self):
        """Optional method to override cache with db data periodically"""
        pass

    async def close(self):
        self._stopping = True

        for t in (self._sync_task, self._reload_task):
            if t and not t.done():
                t.cancel()

        for t in (self._sync_task, self._reload_task):
            if t:
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass

        try:
            await self.sync()
        except Exception:
            pass
