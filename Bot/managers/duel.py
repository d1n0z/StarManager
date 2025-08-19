import asyncio
import time
import traceback
from typing import Dict, Tuple

from Bot.bot import bot
from Bot.managers.base.manager import BaseManager
from config.config import GROUP_ID, api


class TimedAsyncLock:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.last_used = time.time()
        self.failure_count = 0
        self.locked = self._lock.locked

    async def acquire(self):
        await self._lock.acquire()
        self.last_used = time.time()

    def release(self):
        self._lock.release()
        self.last_used = time.time()

    async def __aenter__(self):
        await self._lock.acquire()
        self.last_used = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
        self.last_used = time.time()


class DuelLockManager(BaseManager):
    def __init__(self, ttl: int = 3600):
        super().__init__()
        self._locks: Dict[Tuple[int, int], TimedAsyncLock] = {}
        self._ttl = ttl
        self._cleanup_interval = 600
        self._cleanup_task = bot.loop_wrapper.add_task(self._cleanup_loop)

    def _cache_key(self, chat_id: int, cmid: int):
        return (chat_id, cmid)

    def get_lock(self, chat_id: int, cmid: int):
        print("test")
        key = self._cache_key(chat_id, cmid)
        if key not in self._locks:
            self._locks[key] = TimedAsyncLock()
        else:
            self._locks[key].last_used = time.time()
        return self._locks[key]

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(self._cleanup_interval)
            try:
                await self._cleanup()
            except Exception:
                traceback.print_exc()

    async def _cleanup(self):
        now = time.time()
        to_delete = []

        for key, lock in self._locks.items():
            if lock.locked() or now - lock.last_used <= self._ttl:
                continue

            chat_id, cmid = key
            try:
                await api.messages.delete(
                    group_id=GROUP_ID,
                    delete_for_all=True,
                    peer_id=chat_id + 2000000000,
                    cmids=cmid,
                )
            except Exception:
                try:
                    await api.messages.edit(
                        peer_id=chat_id + 2000000000,
                        message="⌛ Данная дуэль была просрочена.",
                        disable_mentions=1,
                        conversation_message_id=cmid,
                    )
                except Exception:
                    lock.failure_count += 1
                    if lock.failure_count >= 3:
                        to_delete.append(key)
                    continue
                else:
                    to_delete.append(key)
            else:
                to_delete.append(key)

        for key in to_delete:
            del self._locks[key]
