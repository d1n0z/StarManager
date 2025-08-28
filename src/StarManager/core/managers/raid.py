import time
from typing import Dict, Literal, TypeAlias

from cachetools import TTLCache

from StarManager.core.managers.base.manager import BaseManager

EventType: TypeAlias = Literal["chat_invite_user_by_link", "chat_invite_user"]


class RaidManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._link_cache: TTLCache[int, Dict[int, float]] = TTLCache(
            maxsize=50000, ttl=120
        )
        self._invite_cache: TTLCache[int, Dict[int, float]] = TTLCache(
            maxsize=50000, ttl=120
        )
    
    def _get_cache(self, event_type: EventType):
        return self._invite_cache if event_type == "chat_invite_user" else self._link_cache
    
    def _ensure(self, event_type: EventType, chat_id: int) -> Dict[int, float]:
        return self._get_cache(event_type).setdefault(chat_id, {})

    def _clean(self, event_type: EventType, chat_id: int, time_shift: int = 120):
        valid_from = time.time() - time_shift
        user_dict = self._ensure(event_type, chat_id)

        while user_dict and min(user_dict.values()) < valid_from:
            oldest_key = min(user_dict.keys(), key=lambda x: user_dict[x])
            user_dict.pop(oldest_key)

    def get_users(self, event_type: EventType, chat_id: int, time_shift: int):
        self._clean(event_type, chat_id, time_shift)
        return self._ensure(event_type, chat_id)

    def add_user_id(self, event_type: EventType, chat_id: int, uid: int):
        self._ensure(event_type, chat_id)[uid] = time.time()
