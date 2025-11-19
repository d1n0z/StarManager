import asyncio
import random
from typing import List, Tuple, Dict, Any, Optional

import asyncpg
from loguru import logger
from StarManager.core.config import api

MAX_CONCURRENCY = 1
BATCH_SIZE = 499
MAX_RETRIES = 4
JITTER = 0.25

async def safe_api_call(func, *args, max_retries: int = MAX_RETRIES, **kwargs):
    attempt = 0
    while True:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            attempt += 1
            logger.warning(f'API call {getattr(func, "__name__", func)} failed (attempt {attempt}/{max_retries}): {e}')
            if attempt >= max_retries:
                logger.exception("API call exhausted retries")
                raise
            backoff = min(2 ** attempt + random.random() * JITTER, 10)
            await asyncio.sleep(backoff)


def chunks_iterable(items: List[Any], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def process_group_batch(batch_group_ids: List[int]):
    try:
        res = await safe_api_call(api.groups.get_by_id, group_ids=batch_group_ids)
    except Exception:
        logger.exception("groups.get_by_id failed for batch")
        return []

    updates: List[Tuple[str, int]] = []

    groups_list = None
    if res is None:
        groups_list = []
    elif isinstance(res, list):
        groups_list = res
    elif isinstance(res, dict) and "response" in res:
        r = res["response"]
        if isinstance(r, list):
            groups_list = r
        elif isinstance(r, dict) and "items" in r:
            groups_list = r["items"]
        else:
            groups_list = []
    elif hasattr(res, "groups"):
        groups_list = getattr(res, "groups")
    else:
        try:
            groups_list = list(res)
        except Exception:
            groups_list = []

    for g in groups_list or []:
        try:
            if isinstance(g, dict):
                name = g.get("name")
                gid = g.get("id") or g.get("group_id") or g.get("screen_name")
            else:
                name = getattr(g, "name", None)
                gid = getattr(g, "id", None)
            if name is None or gid is None:
                continue
            updates.append((name, -abs(int(gid))))
        except Exception:
            continue

    return updates


async def updateGroups(conn: asyncpg.Connection):
    rows = await conn.fetch("SELECT group_id FROM groupnames")
    if not rows:
        return

    all_ids = list({-abs(r["group_id"]) for r in rows})
    if not all_ids:
        return

    db_rows = await conn.fetch("SELECT group_id, name FROM groupnames")
    db_map: Dict[int, Optional[str]] = {r["group_id"]: r["name"] for r in db_rows}

    batches = []
    for batch in chunks_iterable(all_ids, BATCH_SIZE):
        batches.append([abs(gid) for gid in batch])

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = []
    for batch in batches:
        async def _task(b):
            async with sem:
                return await process_group_batch(b)
        tasks.append(_task(batch))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    name_map: Dict[int, str] = {}
    for res in results:
        if isinstance(res, (Exception, BaseException)):
            continue
        for name, gid in res:
            name_map[gid] = name

    updates: List[Tuple[str, int]] = []
    for gid, name in name_map.items():
        if db_map.get(gid) != name:
            updates.append((name, gid))

    if not updates:
        return

    names_list, ids_list = zip(*updates)
    async with conn.transaction():
        await conn.execute(
            """
            UPDATE groupnames AS g
            SET name = u.name
            FROM UNNEST($1::text[], $2::int[]) AS u(name, group_id)
            WHERE g.group_id = u.group_id
            """,
            list(names_list),
            list(ids_list),
        )
