import asyncio
import json
import random
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from StarManager.core.config import api

MAX_CONCURRENCY = 3
INITIAL_CHUNK = 100
MAX_CODE_LEN = 180_000
MAX_RETRIES = 4
FALLBACK_CONCURRENCY = 5
JITTER = 0.3


def build_conv_script(peer_ids: List[int]) -> str:
    return f"""var peer_ids = {json.dumps(peer_ids)};
return API.messages.getConversationsById({{ peer_ids: peer_ids }}).items;"""


def build_members_script(peer_ids: List[int]) -> str:
    return f"""var peer_ids = {json.dumps(peer_ids)};
var result = [];
var i = 0;
while (i < peer_ids.length) {{
    var id = peer_ids[i];
    var m = API.messages.getConversationMembers({{ peer_id: id }});
    result.push({{peer_id: id, count: m.count}});
    i = i + 1;
}}
return result;"""


async def safe_execute(code: str, max_retries: int = MAX_RETRIES) -> Any:
    attempt = 0
    while True:
        try:
            resp = await api.execute(code=code)
            return resp
        except Exception as e:
            attempt += 1
            msg = str(e)
            logger.warning(f"execute failed (attempt {attempt}/{max_retries}): {msg}")
            if attempt >= max_retries:
                logger.exception("execute exhausted retries")
                raise
            backoff = min(2**attempt + random.random() * JITTER, 10)
            await asyncio.sleep(backoff)


def approx_code_len_for_peer_ids(peer_ids: List[int]) -> int:
    return len(json.dumps(peer_ids)) + 300


def make_chunks_adaptive(
    all_ids: List[int],
    start_chunk: int = INITIAL_CHUNK,
    max_code_len: int = MAX_CODE_LEN,
):
    chunks = []
    n = len(all_ids)
    i = 0
    chunk_size = start_chunk
    while i < n:
        while True:
            end = min(i + chunk_size, n)
            peer_ids = [2000000000 + cid for cid in all_ids[i:end]]
            if approx_code_len_for_peer_ids(peer_ids) <= max_code_len:
                break
            chunk_size = max(5, chunk_size // 2)
        chunks.append(all_ids[i:end])
        i = end
    return chunks


async def fallback_get_members(peer_ids: List[int]) -> List[Tuple[int, Optional[Any]]]:
    sem = asyncio.Semaphore(FALLBACK_CONCURRENCY)

    async def _get_one(pid: int):
        async with sem:
            try:
                r = await api.messages.get_conversation_members(peer_id=pid)
                cnt = None
                if isinstance(r, dict):
                    cnt = r.get("count")
                else:
                    cnt = getattr(r, "count", None)
                if isinstance(cnt, str):
                    cnt = int(cnt)
                return pid, cnt
            except Exception:
                return pid, None

    tasks = [_get_one(pid) for pid in peer_ids]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return results


async def process_chunk(
    chunk_ids: List[int], semaphore: asyncio.Semaphore, db_counts: Dict
) -> Tuple[List[Tuple[str, int]], List[Tuple[int, int]]]:
    peer_ids = [2000000000 + cid for cid in chunk_ids]

    async with semaphore:
        conv_code = build_conv_script(peer_ids)
        try:
            conv_items = await safe_execute(conv_code)
        except Exception:
            logger.warning(
                "execute for conversations failed, trying API method per-call"
            )
            try:
                conv_items = await api.messages.get_conversations_by_id(
                    peer_ids=peer_ids
                )
            except Exception:
                logger.exception("fallback get_conversations_by_id failed:")
                conv_items = None

        updates_chatnames: List[Tuple[str, int]] = []
        conv_iter = []
        if conv_items is None:
            conv_iter = []
        elif isinstance(conv_items, dict) and "items" in conv_items:
            conv_iter = conv_items["items"]
        else:
            conv_iter = conv_items

        for item in conv_iter or []:
            try:
                if isinstance(item, dict):
                    peer = item.get("peer", {})
                    chat_settings = item.get("chat_settings")
                    pid = peer.get("id")
                    if chat_settings and pid:
                        title = chat_settings.get("title")
                        if title:
                            updates_chatnames.append((title, pid - 2000000000))
                else:
                    peer = getattr(item, "peer", None)
                    chat_settings = getattr(item, "chat_settings", None)
                    if peer and chat_settings:
                        pid = getattr(peer, "id", None)
                        title = getattr(chat_settings, "title", None)
                        if pid and title:
                            updates_chatnames.append((title, pid - 2000000000))
            except Exception:
                logger.debug("Error parsing conv item")
                continue

        members_code = build_members_script(peer_ids)
        members_ok = True
        try:
            members_res = await safe_execute(members_code)
        except Exception:
            logger.warning(
                "execute for members failed; will fallback to per-chat calls"
            )
            members_ok = False
            members_res = None

        updates_publicchats: List[Tuple[Optional[int], int]] = []

        if members_ok and members_res:
            for m in members_res:
                try:
                    if isinstance(m, dict):
                        pid = m.get("peer_id")
                        cnt = m.get("count")
                    else:
                        pid = getattr(m, "peer_id", None)
                        cnt = getattr(m, "count", None)
                    if pid is None:
                        continue
                    updates_publicchats.append(
                        (int(cnt) if cnt is not None else None, pid - 2000000000)
                    )
                except Exception:
                    logger.debug("Error parsing members item")
                    continue
        else:
            fallback_peer_ids = peer_ids
            fallback_results = await fallback_get_members(fallback_peer_ids)
            for pid, cnt in fallback_results:
                updates_publicchats.append(
                    (int(cnt) if cnt is not None else None, pid - 2000000000)
                )

        updates_publicchats_filtered = [
            (cnt, cid) for cnt, cid in updates_publicchats if db_counts.get(cid) != cnt and cnt is not None
        ]

        return updates_chatnames, updates_publicchats_filtered


async def update_chats(conn):
    rows = await conn.fetch("SELECT chat_id FROM chatnames")
    chatnames_ids = [r["chat_id"] for r in rows]
    rows = await conn.fetch("SELECT chat_id, members_count FROM publicchats")
    public_ids = [r["chat_id"] for r in rows]

    total_ids = list(set(chatnames_ids + public_ids))
    if not total_ids:
        return

    db_names_rows = await conn.fetch("SELECT chat_id, name FROM chatnames")
    db_names: Dict[int, str] = {r["chat_id"]: r["name"] for r in db_names_rows}
    db_counts_rows = await conn.fetch("SELECT chat_id, members_count FROM publicchats")
    db_counts: Dict[int, Optional[int]] = {
        r["chat_id"]: r["members_count"] for r in db_counts_rows
    }

    chunks = make_chunks_adaptive(
        total_ids, start_chunk=INITIAL_CHUNK, max_code_len=MAX_CODE_LEN
    )

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [process_chunk(chunk, sem, db_counts) for chunk in chunks]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    upd_names: List[Tuple[str, int]] = []
    upd_counts: List[Tuple[int, int]] = []

    name_map: Dict[int, str] = {}
    counts_map: Dict[int, int] = {}

    for res in results:
        if isinstance(res, (Exception, BaseException)):
            continue
        names, counts = res
        for title, cid in names:
            name_map[cid] = title
        for cnt, cid in counts:
            counts_map[cid] = cnt

    for cid, title in name_map.items():
        if db_names.get(cid) != title:
            upd_names.append((title, cid))
    for cid, cnt in counts_map.items():
        if db_counts.get(cid) != cnt:
            upd_counts.append((cnt, cid))

    async with conn.transaction():
        if upd_names:
            names_list, ids_list = zip(*upd_names)
            await conn.execute(
                """UPDATE chatnames AS c
SET name = u.name
FROM UNNEST($1::text[], $2::int[]) AS u(name, chat_id)
WHERE c.chat_id = u.chat_id""",
                list(names_list),
                list(ids_list),
            )

        if upd_counts:
            counts_list, ids_list = zip(*upd_counts)
            await conn.execute(
                """UPDATE publicchats AS p
SET members_count = u.count
FROM UNNEST($1::int[], $2::int[]) AS u(count, chat_id)
WHERE p.chat_id = u.chat_id""",
                list(counts_list),
                list(ids_list),
            )
