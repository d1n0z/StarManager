import asyncio
import json
from typing import Any

from aiolimiter import AsyncLimiter
from loguru import logger

from StarManager.core.config import api

execute_limiter = AsyncLimiter(5, 1)


async def vk_execute(code: str, retry: int = 0) -> Any:
    try:
        async with execute_limiter:
            response = await api.execute(code=code)
            if response:
                if not isinstance(response, (dict, list, tuple)) and hasattr(response, "response"):
                    response = response.response
                    if 'response' in response:
                        response = response['response']
                if isinstance(response, tuple) and response[0] == 'response' and len(response) > 1:
                    response = response[1]
            return response
    except Exception as e:
        msg = str(e).lower()
        if retry < 6 and "internal server" not in msg:
            logger.error(f"vk_execute error: {e}")
        if any(i in msg for i in ("too many", "internal server")) and retry < 6:
            await asyncio.sleep((2**retry) / 2)
            return await vk_execute(code, retry + 1)
        if "internal server" in msg:
            return None
        raise


def build_get_conversations_code(peer_ids_chunk: list[list[int]]) -> str:
    calls = ",".join(
        [
            f"API.messages.getConversationsById({{peer_ids:{json.dumps(peer_ids)}}})"
            for peer_ids in peer_ids_chunk
        ]
    )
    return f"return [{calls}];"


def build_get_conversation_members_code(peer_ids: list[int]) -> str:
    calls = ",".join(
        [
            f'"{peer_id}": API.messages.getConversationMembers({{peer_id: {peer_id}}})'
            for peer_id in peer_ids
        ]
    )
    return f"return {{{calls}}};"


def make_chunks(ids: list[int], base=100):
    for i in range(0, len(ids), base * 25):
        chunk = []
        for y in range(i, i + base * 25, base):
            raw_chunk = ids[y : y + base]
            if not raw_chunk:
                break
            chunk.append([2000000000 + cid for cid in raw_chunk])
        yield chunk


def make_minor_chunks(ids: list[int], base=25):
    for i in range(0, len(ids), base):
        yield ids[i : i + base]


async def updateChats(conn):
    all_chat_ids = await conn.fetchval(
        "SELECT ARRAY(SELECT chat_id FROM chatnames UNION SELECT chat_id FROM publicchats)"
    )
    if not all_chat_ids:
        return

    db_names = {
        r["chat_id"]: r["name"]
        for r in await conn.fetch("SELECT chat_id, name FROM chatnames")
    }
    db_counts = {
        r["chat_id"]: r["members_count"]
        for r in await conn.fetch("SELECT chat_id, members_count FROM publicchats")
    }

    to_update_names: list[tuple[str, int]] = []
    to_update_counts: list[tuple[int, int]] = []

    for peer_ids_chunk in make_chunks(all_chat_ids):
        try:
            convs = await vk_execute(build_get_conversations_code(peer_ids_chunk))
        except Exception:
            convs = None
            logger.exception("failed to get conversations:")

        for item in convs or []:
            if not item or "execute_errors" in item:
                continue
            for chat in item.get("items", []):
                try:
                    pid = int(chat.get("peer", {}).get("id")) - 2000000000
                    title = chat.get("chat_settings", {}).get("title")
                    if title and pid in db_names and db_names[pid] != title:
                        to_update_names.append((title, pid))
                except Exception:
                    logger.exception("failed to update chats:")

        for major in peer_ids_chunk:
            for minor in make_minor_chunks(major):
                try:
                    members = await vk_execute(
                        build_get_conversation_members_code(minor)
                    )
                except Exception:
                    logger.exception("failed to get members:")
                    continue
                for pid, item in (members or {}).items():
                    if not item or "execute_errors" in item:
                        continue
                    try:
                        pid = int(pid) - 2000000000
                        count = item.get("count")
                        if count is not None and pid in db_counts and db_counts[pid] != (
                            count := int(count)
                        ):
                            to_update_counts.append((count, pid))
                    except Exception:
                        logger.exception("failed to update members count:")

    async with conn.transaction():
        if to_update_names:
            for i in range(0, len(to_update_names), 500):
                await conn.executemany(
                    "UPDATE chatnames SET name = $1 WHERE chat_id = $2",
                    to_update_names[i : i + 500],
                )
        if to_update_counts:
            for i in range(0, len(to_update_counts), 500):
                await conn.executemany(
                    "UPDATE publicchats SET members_count = $1 WHERE chat_id = $2",
                    to_update_counts[i : i + 500],
                )
