import asyncio
import html
import os
import random
import string
import subprocess
import time
import traceback
from collections import defaultdict
from datetime import datetime

import yadisk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from vkbottle_types.objects import UsersFields

import keyboard
import messages
from Bot.tgbot import tgbot
from Bot.utils import (
    chunks,
    deleteMessages,
    generateEasyProblem,
    generateHardProblem,
    generateMediumProblem,
    getUserName,
    punish,
    sendMessage,
)
from config.config import (
    DATABASE,
    GROUP_ID,
    MATHGIVEAWAYS_TO,
    PASSWORD,
    PATH,
    PHOTO_NOT_FOUND,
    TG_BACKUP_THREAD_ID,
    TG_CHAT_ID,
    TG_SCHEDULER_THREAD,
    USER,
    YANDEX_TOKEN,
    api,
    vk_api_session,
)
from db import pool

task_locks = defaultdict(asyncio.Lock)


def format_exception_for_telegram(exc: BaseException) -> str:
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    header = "⚠️ Scheduler exception!\n"

    tb = html.escape(tb)
    code_block_start = "<pre><code>"
    code_block_end = "</code></pre>"

    body = f"{code_block_start}{tb}{code_block_end}"
    full_message = f"{header}{body}"

    if len(full_message) > 2**12:
        excess = len(full_message) - 2**12
        tb_lines = tb.splitlines()
        trimmed_tb = "\n".join(tb_lines)
        while excess > 0 and len(tb_lines) > 1:
            tb_lines.pop(0)
            trimmed_tb = "\n".join(tb_lines)
            body = (
                f"{code_block_start}... (output trimmed)\n{trimmed_tb}{code_block_end}"
            )
            full_message = f"{header}{body}"
            excess = len(full_message) - 2**12

    return full_message


async def with_lock(func, use_db=True):
    lock = task_locks[func.__name__]
    if lock.locked():
        return
    async with lock:
        try:
            if use_db:
                async with (await pool()).acquire() as conn:
                    await func(conn)
            else:
                await func()
        except Exception as e:
            logger.exception("Exception traceback:")
            await tgbot.send_message(
                chat_id=TG_CHAT_ID,
                message_thread_id=int(TG_SCHEDULER_THREAD),
                text=format_exception_for_telegram(e),
                parse_mode="HTML",
            )


def schedule(coro_func, *, use_db: bool = True):
    async def _runner():
        try:
            await with_lock(coro_func, use_db=use_db)
        except Exception:
            pass

    return _runner


async def backup():
    now = datetime.now().isoformat(timespec="seconds")
    filename = f"{DATABASE}-{now}.sql.gz"
    os.system(f"sudo rm {PATH}{DATABASE}-*.sql.gz > /dev/null 2>&1")
    subprocess.run(
        f'PGPASSWORD="{PASSWORD}" pg_dump -h localhost -U {USER} {DATABASE} | gzip > {filename}',
        shell=True,
    )
    drive = yadisk.AsyncClient(token=YANDEX_TOKEN)
    async with drive:
        await drive.upload(
            filename,
            f"/StarManager/backups/{filename}",
            timeout=int(os.stat(filename).st_size / 1000 / 128) * 1.5,
        )
        link = await drive.get_download_link(f"/StarManager/backups/{filename}")
    await tgbot.send_message(
        chat_id=TG_CHAT_ID,
        message_thread_id=TG_BACKUP_THREAD_ID,
        text=f"<a href='{link}'>{filename}</a>",
        parse_mode="HTML",
    )
    os.remove(filename)


async def updateInfo(conn):
    user_rows = await conn.fetch("select uid from usernames")
    for i in range(0, len(user_rows), 25):
        batch = [r[0] for r in user_rows[i : i + 25]]
        code = f"""
        var users = API.users.get({{"user_ids": "{",".join(map(str, batch))}", "fields": "domain"}});
        return users;
        """
        try:
            result = vk_api_session.method("execute", {"code": code})
            updates = []
            for u in result["items"]:
                full_name = f"{u['first_name']} {u['last_name']}"
                domain = u.get("domain", f"id{u['id']}")
                updates.append((full_name, domain, u["id"]))
            await conn.executemany(
                "update usernames set name = $1, domain = $2 where uid = $3", updates
            )
        except Exception:
            logger.exception("Users update exception:")

    chat_rows = await conn.fetch("select chat_id from chatnames")
    for i in range(0, len(chat_rows), 100):
        batch = [r[0] for r in chat_rows[i : i + 100]]
        peer_ids = ",".join(str(2000000000 + cid) for cid in batch)
        code = f"""
        var conv = API.messages.getConversationsById({{"peer_ids": "{peer_ids}"}});
        return conv;
        """
        try:
            result = vk_api_session.method("execute", {"code": code})
            updates = []
            for item in result["items"]:
                pid = item["peer"]["id"] - 2000000000
                title = item["chat_settings"]["title"]
                updates.append((title, pid))
            await conn.executemany(
                "update chatnames set name = $1 where chat_id = $2", updates
            )
        except Exception:
            logger.exception("Chats update exception:")

    group_rows = await conn.fetch("select group_id from groupnames")
    for i in range(0, len(group_rows), 500):
        batch = [r[0] for r in group_rows[i : i + 500]]
        code = f"""
        var grp = API.groups.getById({{"group_ids": "{",".join(map(str, map(abs, batch)))}"}});
        return grp;
        """
        try:
            result = vk_api_session.method("execute", {"code": code})
            updates = []
            for g in result["items"]:
                gid = -abs(g["id"])
                updates.append((g["name"], gid))
            await conn.executemany(
                "update groupnames set name = $1 where group_id = $2", updates
            )
        except Exception:
            logger.exception("Groups update exception:")


async def every10min(conn):
    now = time.time()
    expired = await conn.fetch(
        "SELECT uid, cmid FROM premiumexpirenotified WHERE date < $1",
        now - 86400 * 2,
    )
    if expired:
        await asyncio.gather(*(deleteMessages(cmid, uid) for uid, cmid in expired))
        await conn.execute(
            "DELETE FROM premiumexpirenotified WHERE date < $1", now - 86400 * 2
        )

    notified = {
        row[0] for row in await conn.fetch("SELECT uid FROM premiumexpirenotified")
    }
    expiring = await conn.fetch(
        "SELECT uid FROM premium WHERE time < $1 AND time > $2 AND uid != ALL($3)",
        now + 86400 * 3,
        now + 86400 * 2,
        list(notified),
    )
    for (uid,) in expiring:
        promo = None
        while not promo or await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM prempromo WHERE promo = $1)", promo
        ):
            promo = "".join(
                random.choice(string.ascii_letters + string.digits) for _ in range(8)
            )
        exp = datetime.fromtimestamp(now + 86400 * 2)
        await conn.execute(
            'INSERT INTO prempromo (promo, val, start, "end", uid) VALUES ($1, $2, $3, $4, $5)',
            promo,
            25,
            now,
            exp.replace(hour=0, minute=0).timestamp(),
            uid,
        )
        cmid = (
            await sendMessage(
                uid,
                messages.premium_expire(
                    uid, await getUserName(uid), exp.strftime("%d.%m.%Y / 00:00")
                ),
                keyboard.premium_expire(promo),
            )
        )[0].conversation_message_id
        await conn.execute(
            "INSERT INTO premiumexpirenotified (uid, date, cmid) VALUES ($1, $2, $3)",
            uid,
            now,
            cmid,
        )

    await conn.execute(
        """
                    WITH affected AS (
                        SELECT b.id, b.streak
                        FROM bonus b
                        WHERE b.time < $1
                        AND NOT EXISTS (SELECT 1 FROM premium p WHERE p.uid = b.uid)
                        FOR UPDATE SKIP LOCKED
                    ),
                    updated AS (
                        UPDATE bonus
                        SET streak = streak - 2, time = $2
                        WHERE id IN (SELECT id FROM affected WHERE streak >= 2)
                        RETURNING id
                    )
                    DELETE FROM bonus
                    WHERE id IN (SELECT id FROM affected WHERE streak < 2);
                    """,
        now - 172800,
        now - 86400,
    )

    for chunk in chunks(
        await conn.fetch("SELECT uid FROM rewardscollected WHERE deactivated = false"),
        499,
    ):
        try:
            members = await api.groups.is_member(
                group_id=GROUP_ID, user_ids=[row[0] for row in chunk]
            )
            to_deactivate = [m.user_id for m in members if not m.member]
            if to_deactivate:
                await conn.execute(
                    "UPDATE rewardscollected SET deactivated = true WHERE uid = ANY($1)",
                    to_deactivate,
                )
        except Exception:
            pass


async def everyminute(conn):
    now = time.time()
    os.system(f"find {PATH}media/temp/ -mtime +1 -exec rm {{}} \;")
    await conn.execute("DELETE FROM premium WHERE time < $1", now)

    captchas = await conn.fetch(
        "SELECT uid, chat_id FROM captcha WHERE exptime < $1", now
    )
    unique = set()
    for uid, chat_id in captchas:
        if (uid, chat_id) in unique:
            continue
        if await conn.fetchval(
            "DELETE FROM typequeue WHERE chat_id = $1 AND uid = $2 AND type = 'captcha' RETURNING 1",
            chat_id,
            uid,
        ):
            unique.add((uid, chat_id))
            s = await conn.fetchrow(
                "SELECT id, punishment FROM settings WHERE chat_id = $1 AND setting = 'captcha'",
                chat_id,
            )
            await punish(uid, chat_id, s[0])
            await sendMessage(
                chat_id + 2000000000,
                messages.captcha_punish(uid, await getUserName(uid), s[1]),
            )

    await conn.execute("DELETE FROM captcha WHERE exptime < $1", now)
    await conn.execute('DELETE FROM prempromo WHERE "end" < $1', now)

    todelete = await conn.fetch(
        "SELECT peerid, cmid FROM todelete WHERE delete_at < $1", now
    )
    if todelete:
        await asyncio.gather(
            *(deleteMessages(cmid, peerid - 2000000000) for peerid, cmid in todelete)
        )
        await conn.execute("DELETE FROM todelete WHERE delete_at < $1", now)


async def run_notifications(conn):
    rows = await conn.fetch(
        "SELECT id, chat_id, tag, every, time, name, text FROM notifications WHERE status = 1 AND every != -1"
    )
    for row in rows:
        id_, chat_id, tag, every, ttime, name, text = row
        try:
            if await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM blocked WHERE uid = $1 AND type = 'chat')",
                chat_id,
            ):
                continue
            if ttime >= time.time():
                continue
            call = False
            if tag == 1:
                call = True
            elif tag == 2:
                try:
                    members = await api.messages.get_conversation_members(
                        chat_id + 2000000000
                    )
                    call = "".join(
                        f"[id{m.member_id}|\u200b\u206c]"
                        for m in members.items
                        if m.member_id > 0
                    )
                except Exception:
                    pass
            elif tag == 3:
                ac = await conn.fetch(
                    "SELECT uid FROM accesslvl WHERE chat_id = $1 AND access_level > 0 AND uid > 0",
                    chat_id,
                )
                call = "".join(f"[id{a[0]}|\u200b\u206c]" for a in ac)
            else:
                ac = await conn.fetch(
                    "SELECT uid FROM accesslvl WHERE chat_id = $1 AND access_level > 0 AND uid > 0",
                    chat_id,
                )
                excluded = {a[0] for a in ac}
                try:
                    members = await api.messages.get_conversation_members(
                        chat_id + 2000000000
                    )
                    call = "".join(
                        f"[id{m.member_id}|\u200b\u206c]"
                        for m in members.items
                        if m.member_id > 0 and m.member_id not in excluded
                    )
                except Exception:
                    pass
            if call:
                if not await sendMessage(
                    chat_id + 2000000000, messages.send_notification(text, call)
                ):
                    await sendMessage(
                        chat_id + 2000000000,
                        messages.notification_too_long_text(name),
                    )
            await conn.execute(
                "UPDATE notifications SET status = $1, time = $2 WHERE id = $3",
                0 if not every else 1,
                int(ttime + (every * 60)) if every else ttime,
                id_,
            )
        except Exception:
            traceback.print_exc()


async def run_nightmode_notifications(conn):
    rows = await conn.fetch(
        "SELECT chat_id, value2 FROM settings WHERE setting = 'nightmode' AND pos = true AND value2 IS NOT NULL"
    )
    now = datetime.now()
    for chat_id, value in rows:
        if await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM blocked WHERE uid = $1 AND type = 'chat')",
            chat_id,
        ):
            continue
        start_str, end_str = value.split("-")
        start = datetime.strptime(start_str, "%H:%M").replace(year=2024)
        end = datetime.strptime(end_str, "%H:%M").replace(year=2024)
        if now.hour == start.hour and now.minute == start.minute:
            await sendMessage(
                chat_id + 2000000000,
                messages.nightmode_start(
                    start.strftime("%H:%M"), end.strftime("%H:%M")
                ),
            )
        elif now.hour == end.hour and now.minute == end.minute:
            await sendMessage(chat_id + 2000000000, messages.nightmode_end())


async def mathgiveaway(conn):
    now = datetime.now()
    if now.hour in (9, 21) and now.minute < 15:
        math, ans = generateHardProblem()
        level, xp = 2, random.randint(1000, 1200)
    elif now.hour in range(0, 23, 2) and now.minute < 15:
        math, ans = generateMediumProblem()
        level, xp = 1, random.randint(500, 800)
    else:
        math, ans = generateEasyProblem()
        level, xp = 0, random.randint(200, 400)

    old = [
        row[0]
        for row in await conn.fetch(
            "SELECT cmid FROM mathgiveaway WHERE finished = false"
        )
    ]
    if old:
        await deleteMessages(old, MATHGIVEAWAYS_TO)
    await conn.execute("UPDATE mathgiveaway SET finished = true WHERE finished = false")
    cmid = (
        await sendMessage(
            MATHGIVEAWAYS_TO + 2000000000,
            messages.math_problem(math, level, xp),
        )
    )[0].conversation_message_id
    await conn.execute(
        "INSERT INTO mathgiveaway (math, level, cmid, xp, ans, winner, finished) VALUES ($1, $2, $3, $4, $5, NULL, false)",
        math,
        level,
        cmid,
        xp,
        ans,
    )


async def everyday(conn):
    await conn.execute("UPDATE xp SET coins_limit=0")


async def run():
    scheduler = AsyncIOScheduler(timezone="GMT+3")

    logger.info("loading tasks")

    scheduler.add_job(
        schedule(run_notifications), CronTrigger.from_crontab("*/1 * * * *")
    )
    scheduler.add_job(
        schedule(run_nightmode_notifications), CronTrigger.from_crontab("*/1 * * * *")
    )
    scheduler.add_job(schedule(everyminute), CronTrigger.from_crontab("*/1 * * * *"))

    scheduler.add_job(schedule(every10min), CronTrigger.from_crontab("*/10 * * * *"))

    scheduler.add_job(
        schedule(backup, use_db=False), CronTrigger.from_crontab("0 6,18 * * *")
    )

    scheduler.add_job(schedule(updateInfo), CronTrigger.from_crontab("0 */3 * * *"))

    scheduler.add_job(schedule(mathgiveaway), CronTrigger.from_crontab("*/15 * * * *"))

    scheduler.add_job(schedule(everyday), CronTrigger.from_crontab("0 0 * * *"))

    scheduler.start()
