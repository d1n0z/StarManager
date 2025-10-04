import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, TypeAlias

from StarManager.core.managers.base import BaseCachedModel, BaseManager
from StarManager.core.utils import api, settings

CacheKey: TypeAlias = Tuple[int, int]


@dataclass
class _CachedRPS(BaseCachedModel):
    start_timestamp: float
    created_by: int
    second_player_id: Optional[int] = None
    first_player_pick: Optional[str] = None  # the first player is who created the game
    second_player_pick: Optional[str] = None  # the second player is who pressed the button


class RPSManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._games: Dict[CacheKey, _CachedRPS] = {}
        self._clean_task = None

    async def initialize(self):
        self._start_clean_task()

    def _start_clean_task(self):
        if not self._clean_task:
            self._clean_task = asyncio.create_task(self._clean_loop())

    async def _clean_loop(self):
        while True:
            await asyncio.sleep(5)
            await self._clean()

    def _cache_key(self, cmid: int, peer_id: int) -> CacheKey:
        return (cmid, peer_id)

    async def _clean(self):
        to_delete = []
        for key, game in list(self._games.items()):
            cmid, peer_id = key
            if time.time() - game.start_timestamp <= 120:
                continue
            try:
                await api.messages.delete(
                    group_id=settings.vk.group_id,
                    delete_for_all=True,
                    peer_id=peer_id,
                    cmids=[cmid],
                )
            except Exception:
                try:
                    await api.messages.edit(
                        peer_id=peer_id,
                        message="⌛ Данная игра была просрочена.",
                        disable_mentions=True,
                        conversation_message_id=cmid,
                    )
                except Exception:
                    continue
                else:
                    to_delete.append(key)
            else:
                to_delete.append(key)

        for key in to_delete:
            self._games.pop(key, None)

    def get_started_timestamp(self, cmid: int, peer_id: int):
        key = self._cache_key(cmid, peer_id)
        game = self._games.get(key)
        return float(game.start_timestamp) if game else 0.0

    def get_picks(self, cmid: int, peer_id: int):
        key = self._cache_key(cmid, peer_id)
        game = self._games.get(key)
        return (game.first_player_pick, game.second_player_pick) if game else (None, None)

    def get_creator_id(self, cmid: int, peer_id: int):
        key = self._cache_key(cmid, peer_id)
        game = self._games.get(key)
        return game.created_by if game else None

    def get_second_player_id(self, cmid: int, peer_id: int):
        key = self._cache_key(cmid, peer_id)
        game = self._games.get(key)
        return game.second_player_id if game else None

    async def add_game(self, cmid: int, peer_id: int, started_at: float, created_by: int):
        key = self._cache_key(cmid, peer_id)
        async with self._lock:
            self._games[key] = _CachedRPS(start_timestamp=started_at, created_by=created_by)

    async def set_pick(self, cmid: int, peer_id: int, pick: str, is_first_player: bool, second_player_id: Optional[int] = None):
        key = self._cache_key(cmid, peer_id)
        async with self._lock:
            game = self._games.get(key)
            if not game:
                raise ValueError(f"Game not found for cmid={cmid}, peer_id={peer_id}")
            if is_first_player:
                game.first_player_pick = pick
            else:
                game.second_player_pick = pick
                game.second_player_id = second_player_id

    async def remove_game(self, cmid: int, peer_id: int):
        key = self._cache_key(cmid, peer_id)
        async with self._lock:
            self._games.pop(key, None)
