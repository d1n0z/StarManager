import time
from collections import deque
from typing import Tuple

from cachetools import TTLCache

from StarManager.core.managers.base.manager import BaseManager


class AntispamMessagesManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: TTLCache[Tuple[int, int], deque[float]] = TTLCache(
            maxsize=50000, ttl=60
        )

    def _cache_key(self, chat_id: int, uid: int):
        return (chat_id, uid)

    def _clean(self, key):
        valid_from = time.time() - 60
        user_deque = self._cache.setdefault(key, deque())

        while user_deque and user_deque[0] < valid_from:
            user_deque.popleft()

    def get_count(self, chat_id: int, uid: int):
        key = self._cache_key(chat_id, uid)
        self._clean(key)

        return len(self._cache[key])

    def add_message(self, chat_id: int, uid: int, messagetime: float):
        key = self._cache_key(chat_id, uid)
        self._clean(key)

        self._cache[key].append(messagetime)
