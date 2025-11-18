import json

from aiolimiter import AsyncLimiter

from StarManager.core.config import api

execute_limiter = AsyncLimiter(3, 1)
MAX_CODE_LEN = 180_000
CHUNK_BASE = 135


async def vk_execute(code: str):
    async with execute_limiter:
        return await api.execute(code=code)


def build_get_conversations_code(peer_ids: list[int]) -> str:
    return f"return API.messages.getConversationsById({{peer_ids:{json.dumps(peer_ids)}}}).items;"


def build_get_members_code(peer_ids: list[int]) -> str:
    ids = json.dumps(peer_ids)
    return (
        f"var i=0,r=[];while(i<{len(peer_ids)})"
        f"{{r.push(API.messages.getConversationMembers({{peer_id:{ids}[i]}}));i=i+1;}}return r;"
    )


def make_chunks(ids: list[int]) -> list[list[int]]:
    chunks = []
    for i in range(0, len(ids), CHUNK_BASE):
        raw_chunk = ids[i : i + CHUNK_BASE]
        peer_ids = [2000000000 + cid for cid in raw_chunk]
        while len(json.dumps(peer_ids)) > MAX_CODE_LEN - 1500:
            raw_chunk = raw_chunk[:-5]
            peer_ids = peer_ids[:-5]
        chunks.append(peer_ids)
    return chunks


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

    for peer_ids in make_chunks(all_chat_ids):
        local_map = {
            pid: cid for pid, cid in zip(peer_ids, [p - 2000000000 for p in peer_ids])
        }

        convs = await vk_execute(build_get_conversations_code(peer_ids))
        for item in convs or []:
            pid = item.peer.id
            cid = local_map.get(pid)
            if not cid:
                continue
            title = getattr(getattr(item, "chat_settings", None), "title", None)
            if title and db_names.get(cid) != title:
                to_update_names.append((title, cid))

        members_raw = await vk_execute(build_get_members_code(peer_ids))
        for item in members_raw or []:
            pid = getattr(item, "peer_id", None) or item.get("peer_id")
            cid = local_map.get(pid)
            if not cid:
                continue
            count = getattr(item, "count", None) or item.get("count")
            if count is not None and db_counts.get(cid, -1) != count:
                to_update_counts.append((count, cid))

    async with conn.transaction():
        if to_update_names:
            await conn.executemany(
                "UPDATE chatnames SET name = $1 WHERE chat_id = $2", to_update_names
            )
        if to_update_counts:
            await conn.executemany(
                "UPDATE publicchats SET members_count = $1 WHERE chat_id = $2",
                to_update_counts,
            )
