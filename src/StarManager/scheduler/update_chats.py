import asyncio
import json

from StarManager.core.config import api

EXECUTE_RPM = 4
METHODS_RPM = 3
MAX_CODE_LEN = 180_000
CHUNK_BASE = 120


async def rate_limited_execute(code: str):
    resp = await api.execute(code=code)
    await asyncio.sleep(1 / EXECUTE_RPM)
    return resp


async def rate_limited_method(call_func):
    resp = await call_func()
    await asyncio.sleep(1 / METHODS_RPM)
    return resp


def build_get_conversations_code(peer_ids: list[int]) -> str:
    return f'return API.messages.getConversationsById({{peer_ids: {json.dumps(peer_ids)}}}).items;'


def build_get_members_code(peer_ids: list[int]) -> str:
    return f"""var ids = {json.dumps(peer_ids)};
var res = [];
var i = 0;
while (i < ids.length) {{
    res.push(API.messages.getConversationMembers({{peer_id: ids[i]}}));
    i = i + 1;
}}
return res;"""


def make_chunks(ids: list[int]) -> list[list[int]]:
    chunks = []
    for i in range(0, len(ids), CHUNK_BASE):
        chunk = ids[i:i + CHUNK_BASE]
        if len(json.dumps([2000000000 + x for x in chunk])) > MAX_CODE_LEN - 1000:
            chunk = chunk[:-10]
        chunks.append([2000000000 + x for x in chunk])
    return chunks


async def updateChats(conn):
    all_chat_ids = await conn.fetchval("SELECT ARRAY(SELECT chat_id FROM chatnames UNION SELECT chat_id FROM publicchats)")

    if not all_chat_ids:
        return

    db_names = {r["chat_id"]: r["name"] async for r in conn.cursor("SELECT chat_id, name FROM chatnames")}
    db_counts = {r["chat_id"]: r["members_count"] async for r in conn.cursor("SELECT chat_id, members_count FROM publicchats")}

    peer_chunks = make_chunks(all_chat_ids)

    to_update_names = []
    to_update_counts = []

    for peer_ids in peer_chunks:
        convs = await rate_limited_execute(build_get_conversations_code(peer_ids))
        for item in convs:
            pid = item.peer.id
            cid = pid - 2000000000
            title = item.chat_settings.title if item.chat_settings else None
            if title and db_names.get(cid) != title:
                to_update_names.append((title, cid))

        members_list = await rate_limited_execute(build_get_members_code(peer_ids))
        for item in members_list:
            pid = item.peer_id if hasattr(item, "peer_id") else item["peer_id"]
            cid = pid - 2000000000
            count = item.count if hasattr(item, "count") else item["count"]
            if db_counts.get(cid, -1) != count:
                to_update_counts.append((count, cid))

    async with conn.transaction():
        if to_update_names:
            await conn.executemany(
                "UPDATE chatnames SET name = $1 WHERE chat_id = $2",
                to_update_names
            )
        if to_update_counts:
            await conn.executemany(
                "UPDATE publicchats SET members_count = $1 WHERE chat_id = $2",
                to_update_counts
            )
