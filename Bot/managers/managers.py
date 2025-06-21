import time
from typing import Dict, Tuple
from collections import deque


class AntispamMessages:
    def __init__(self):
        self._cache: Dict[Tuple[int, int], deque[float]] = {}
    
    def _cache_key(self, chat_id: int, uid: int) -> Tuple[int, int]:
        return (chat_id, uid)

    def _clean(self, key) -> None:
        valid_from = time.time() - 60
        user_deque = self._cache.setdefault(key, deque())

        while user_deque and user_deque[0] < valid_from:
            user_deque.popleft()

    def get_count(self, chat_id: int, uid: int) -> int:
        key = self._cache_key(chat_id, uid)
        self._clean(key)

        return len(self._cache[key])

    def add_message(self, chat_id: int, uid: int, messagetime: float) -> None:
        key = self._cache_key(chat_id, uid)
        self._clean(key)

        self._cache[key].append(messagetime)
