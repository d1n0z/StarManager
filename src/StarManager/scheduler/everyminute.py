import asyncio
import time
from typing import Iterable, List

import asyncpg
from loguru import logger

from StarManager.core import managers
from StarManager.core.utils import delete_messages, get_user_name, punish, send_message
from StarManager.vkbot import messages

NETWORK_CONCURRENCY = 12


class TTLCache:
    def __init__(self, ttl_sec: int = 60):
        self.ttl = ttl_sec
        self._data = {}

    def get(self, key):
        v = self._data.get(key)
        if not v:
            return None
        val, exp = v
        if time.time() > exp:
            del self._data[key]
            return None
        return val

    def set(self, key, value):
        self._data[key] = (value, time.time() + self.ttl)

    def clear(self):
        self._data.clear()


_chat_settings_cache = TTLCache(ttl_sec=30)
_user_name_cache = TTLCache(ttl_sec=30)


async def gather_with_limit(coros: Iterable, limit: int = NETWORK_CONCURRENCY):
    sem = asyncio.Semaphore(limit)

    async def runner(c):
        async with sem:
            return await c

    tasks = [asyncio.create_task(runner(c)) for c in coros]
    return await asyncio.gather(*tasks, return_exceptions=True)


async def _get_chat_captcha_setting(chat_id: int):
    sval = _chat_settings_cache.get(chat_id)
    if sval is not None:
        return sval
    try:
        s = await managers.chat_settings.get(chat_id, "captcha", ("id", "punishment"))
    except Exception:
        s = None
    _chat_settings_cache.set(chat_id, s)
    return s


async def _get_user_name_cached(uid: int):
    name = _user_name_cache.get(uid)
    if name is not None:
        return name
    try:
        name = await get_user_name(uid)
    except Exception:
        name = "Unknown"
    _user_name_cache.set(uid, name)
    return name


async def everyminute(conn: asyncpg.Connection):
    now = time.time()

    rows = await conn.fetch("SELECT uid, chat_id FROM captcha WHERE exptime < $1", now)
    if rows:
        unique_pairs = []
        seen = set()
        for r in rows:
            pair = (r["chat_id"], r["uid"])
            if pair not in seen:
                seen.add(pair)
                unique_pairs.append(pair)

        if unique_pairs:
            params: List = []
            values_clause_parts: List[str] = []
            idx = 1
            for chat_id, uid in unique_pairs:
                values_clause_parts.append(f"(${idx}::bigint, ${idx + 1}::bigint)")
                params.extend([chat_id, uid])
                idx += 2
            values_clause = ", ".join(values_clause_parts)

            try:
                deleted = await conn.fetch(
                    f"""
WITH removed AS (
  DELETE FROM typequeue t
  USING (VALUES {values_clause}) AS v(chat_id, uid)
  WHERE t.chat_id = v.chat_id AND t.uid = v.uid AND t.type = 'captcha'
  RETURNING t.chat_id, t.uid
)
SELECT chat_id, uid FROM removed;""",
                    *params,
                )
            except Exception:
                deleted = []
                for chat_id, uid in unique_pairs:
                    try:
                        if await conn.fetchval(
                            "DELETE FROM typequeue WHERE chat_id=$1 AND uid=$2 AND type='captcha' RETURNING 1",
                            chat_id,
                            uid,
                        ):
                            deleted.append({"chat_id": chat_id, "uid": uid})
                    except Exception:
                        pass

            tasks = []
            for rec in deleted:
                chat_id = rec["chat_id"]
                uid = rec["uid"]

                async def _handle_one(uid=uid, chat_id=chat_id):
                    s = await _get_chat_captcha_setting(chat_id)
                    if not s:
                        return None
                    punish_id, punishment = s
                    try:
                        await punish(uid, chat_id, punish_id)
                    except Exception:
                        logger.exception("Error in punish for captcha")

                    try:
                        name = await _get_user_name_cached(uid)
                        text = await messages.captcha_punish(uid, name, punishment)
                        await send_message(chat_id + 2000000000, text)
                    except Exception:
                        logger.exception("Failed to notify captcha punishment")
                    return None

                tasks.append(_handle_one())

            if tasks:
                await gather_with_limit(tasks, limit=NETWORK_CONCURRENCY)

    try:
        await conn.execute("DELETE FROM captcha WHERE exptime < $1", now)
    except Exception:
        logger.exception("Failed to delete old captcha rows")

    try:
        rows = await conn.fetch(
            "DELETE FROM todelete WHERE delete_at < $1 RETURNING peerid, cmid", now
        )
    except Exception:
        logger.exception("Failed to fetch todelete rows")
        rows = []

    if rows:
        tasks = []
        for r in rows:
            peerid = r["peerid"] - 2000000000
            cmid = r["cmid"]

            async def _del(cmid=cmid, peerid=peerid):
                try:
                    await delete_messages(cmid, peerid)
                except Exception:
                    logger.exception(
                        "delete_messages failed for cmid=%s peer=%s", cmid, peerid
                    )

            tasks.append(_del())

        if tasks:
            await gather_with_limit(tasks, limit=NETWORK_CONCURRENCY)

    return
