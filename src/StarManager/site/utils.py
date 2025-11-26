import asyncio
import time
from collections import deque

_VK_TIMEOUT_WINDOW = 60 * 30
_vk_timeouts = deque()
_vk_timeouts_lock = asyncio.Lock()


async def _prune_timeouts(now: float):
    cutoff = now - _VK_TIMEOUT_WINDOW
    while _vk_timeouts and _vk_timeouts[0] < cutoff:
        _vk_timeouts.popleft()


async def record_vk_timeout():
    now = time.monotonic()
    async with _vk_timeouts_lock:
        _vk_timeouts.append(now)
        await _prune_timeouts(now)


async def get_vk_timeouts_count():
    now = time.monotonic()
    async with _vk_timeouts_lock:
        await _prune_timeouts(now)
        return len(_vk_timeouts)
