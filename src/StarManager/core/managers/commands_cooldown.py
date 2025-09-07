import time
from typing import Dict

from cachetools import TTLCache

from StarManager.core.config import settings
from StarManager.core.managers.base import BaseManager


class CommandsCooldownManager(BaseManager):
    def __init__(self):
        super().__init__()
        ttl = max(settings.commands.cooldown.values())
        self._cache: TTLCache[int, Dict[str, float]] = TTLCache(maxsize=5000, ttl=ttl)

    def get_user_time(self, uid: int, cmd: str):
        return self._cache.get(uid, {}).get(cmd, 0.0)

    def set(self, uid: int, cmd: str):
        user_cmds = self._cache.setdefault(uid, {})
        user_cmds[cmd] = time.time()
