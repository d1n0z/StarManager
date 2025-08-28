import asyncio
from abc import ABC
from typing import Dict


class BaseManager(ABC):
    def __init__(self):
        self._lock = asyncio.Lock()
        self._cache: Dict = {}
