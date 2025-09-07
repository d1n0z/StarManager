import asyncio
from abc import ABC


class BaseRepository(ABC):
    def __init__(self):
        self._lock = asyncio.Lock()
