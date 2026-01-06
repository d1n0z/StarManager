import asyncio
import html
import os
import random
import string
import time
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Optional

import asyncpg
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from StarManager.core import managers
from StarManager.core.config import api, settings
from StarManager.core.db import pool
from StarManager.core.scheduler_monitor import scheduler_monitor
from StarManager.core.utils import (
    add_user_xp,
    chunks,
    delete_messages,
    generate_easy_problem,
    generate_hard_problem,
    generate_medium_problem,
    get_user_name,
    punish,
    send_message,
)
from StarManager.scheduler.update_chats import updateChats
from StarManager.tgbot import keyboard as tgkeyboard
from StarManager.tgbot.bot import bot as tgbot
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.checkers import getULvlBanned

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


async def with_lock(func, use_db=True, timeout: Optional[int] = 300):
    lock = task_locks[func.__name__]
    if lock.locked():
        logger.warning(f"Task {func.__name__} is already running, skipping")
        return
    async with lock:
        scheduler_monitor.mark_run(func.__name__)
        try:
            if timeout is None:
                if use_db:
                    async with (await pool()).acquire() as conn:
                        await func(conn)
                else:
                    await func()
            else:
                async with asyncio.timeout(timeout):
                    if use_db:
                        async with (await pool()).acquire() as conn:
                            await func(conn)
                    else:
                        await func()
        except asyncio.TimeoutError:
            logger.error(f"Task {func.__name__} timed out after {timeout}s")
            await tgbot.send_message(
                chat_id=settings.telegram.chat_id,
                message_thread_id=int(settings.telegram.scheduler_thread_id),
                text=f"⚠️ Scheduler task <code>{func.__name__}</code> timed out after {timeout}s",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.exception("Exception traceback:")
            await tgbot.send_message(
                chat_id=settings.telegram.chat_id,
                message_thread_id=int(settings.telegram.scheduler_thread_id),
                text=format_exception_for_telegram(e),
                parse_mode="HTML",
            )


def schedule(coro_func, *, use_db: bool = True, timeout: Optional[int] = 300):
    if timeout is not None:
        scheduler_monitor.register_job(coro_func.__name__, timeout)

    async def _runner():
        try:
            await with_lock(coro_func, use_db=use_db, timeout=timeout)
        except Exception:
            pass

    return _runner


async def backup() -> None:
    from StarManager.scheduler.backup_service import backup_service

    await backup_service.create_backup()


async def updateUsers(conn: asyncpg.Connection):  # TODO: optimize
    user_rows = await conn.fetch("select uid from usernames")
    for i in range(0, len(user_rows), 25):
        batch = [r[0] for r in user_rows[i : i + 25]]
        try:
            if i:
                await asyncio.sleep(0.5)
            users = await api.users.get(user_ids=batch, fields=["domain"])  # type: ignore
            updates = []
            for u in users:
                full_name = (
                    f"{u.first_name} {u.last_name}"
                    if u.first_name and u.last_name
                    else "Unknown"
                )
                domain = u.domain or f"id{u.id}"
                updates.append((full_name, domain, u.id))
            await conn.executemany(
                "update usernames set name = $1, domain = $2 where uid = $3", updates
            )
        except Exception:
            logger.exception("Users update exception:")


async def updateGroups(conn: asyncpg.Connection):  # TODO: optimize
    group_rows = await conn.fetch("select group_id from groupnames")
    for i in range(0, len(group_rows), 499):
        batch = [abs(r[0]) for r in group_rows[i : i + 499]]
        try:
            if i:
                await asyncio.sleep(0.5)
            result = await api.groups.get_by_id(group_ids=batch)
            if not result or not result.groups:
                continue
            updates = [(g.name, -abs(g.id)) for g in result.groups]
            await conn.executemany(
                "update groupnames set name = $1 where group_id = $2", updates
            )
        except Exception:
            logger.exception("Groups update exception:")


async def every10min(conn: asyncpg.Connection):
    await asyncio.to_thread(
        os.system,
        rf"find {settings.service.path}src/StarManager/core/media/temp/ -mtime +1 -exec rm {{}} \;",
    )
    now = time.time()
    await conn.execute('DELETE FROM prempromo WHERE "end" < $1', now)
    await managers.premium.delete_expired()
    expired = await conn.fetch(
        "SELECT uid, cmid FROM premiumexpirenotified WHERE date < $1",
        now - 86400 * 2,
    )
    if expired:
        await asyncio.gather(
            *(delete_messages(cmid, uid) for uid, cmid in expired),
            return_exceptions=True,
        )
        await conn.execute(
            "DELETE FROM premiumexpirenotified WHERE date < $1", now - 86400 * 2
        )

    notified = {
        row[0] for row in await conn.fetch("SELECT uid FROM premiumexpirenotified")
    }
    expiring = [i for i in await managers.premium.get_expiring() if i not in notified]
    for uid in expiring:
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
        cmid = await send_message(
            uid,
            await messages.premium_expire(
                uid, await get_user_name(uid), exp.strftime("%d.%m.%Y / 00:00")
            ),
            keyboard.premium_expire(promo),
        )
        if not isinstance(cmid, list):
            continue
        cmid = cmid[0].conversation_message_id
        await conn.execute(
            "INSERT INTO premiumexpirenotified (uid, date, cmid) VALUES ($1, $2, $3)",
            uid,
            now,
            cmid,
        )

    deletes, updates = [], []
    for row in await conn.fetch(
        "SELECT id, time, streak from bonus WHERE time < $1 FOR UPDATE SKIP LOCKED",
        now - 86400 * 2,
    ):
        if row[2] <= 2:
            deletes.append((row[0],))
            continue
        updates.append((row[0],))
    if updates:
        await conn.executemany(
            "UPDATE bonus SET time=time+86400, streak=streak-2 where id=$1", updates
        )
    if deletes:
        await conn.executemany("DELETE FROM bonus WHERE id=$1", deletes)

    for chunk in chunks(await managers.rewardscollected.get_all_activated(), 499):
        try:
            await asyncio.sleep(0.5)
            members = await api.groups.is_member(
                group_id=settings.vk.group_id, user_ids=[row.uid for row in chunk]
            )
            to_deactivate = [m.user_id for m in members if not m.member]
            for uid in to_deactivate:
                await managers.rewardscollected.turn(uid)
        except Exception:
            pass


async def everyminute(conn: asyncpg.Connection):
    now = time.time()

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

            if s := await managers.chat_settings.get(
                chat_id, "captcha", ("id", "punishment")
            ):
                await punish(uid, chat_id, s[0])
                await send_message(
                    chat_id + 2000000000,
                    await messages.captcha_punish(uid, await get_user_name(uid), s[1]),
                )

    await conn.execute("DELETE FROM captcha WHERE exptime < $1", now)

    todelete = await conn.fetch(
        "SELECT peerid, cmid FROM todelete WHERE delete_at < $1", now
    )
    if todelete:
        await asyncio.gather(
            *(delete_messages(cmid, peerid - 2000000000) for peerid, cmid in todelete),
            return_exceptions=True,
        )
        await conn.execute("DELETE FROM todelete WHERE delete_at < $1", now)


async def run_notifications(conn: asyncpg.Connection):
    now = int(time.time())
    rows = await conn.fetch(
        "select id, chat_id, tag, every, time, name, text from notifications where status = 1 and every != -1 and time < $1",
        now,
    )
    for row in rows:
        id_, chat_id, tag, every, ttime, name, text = row
        if await managers.blocked.get(chat_id, "chat"):
            await conn.execute("delete from notifications where chat_id=$1", chat_id)
            continue
        try:
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
            else:
                ac = await managers.access_level.get_all(chat_id=chat_id)
                if tag == 3:
                    call = "".join(f"[id{a.uid}|\u200b\u206c]" for a in ac)
                else:
                    excluded = {a.uid for a in ac}
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
                if not await send_message(
                    chat_id + 2000000000,
                    await messages.send_notification(text, call),
                    disable_mentions=False,
                ):
                    await send_message(
                        chat_id + 2000000000,
                        await messages.notification_too_long_text(name),
                    )
            next = int(ttime + (every * 60))
            while next < time.time() and every > 0:
                next += every * 60
            await conn.execute(
                "UPDATE notifications SET status = $1, time = $2 WHERE id = $3",
                0 if not every else 1,
                next if every else ttime,
                id_,
            )
        except Exception:
            traceback.print_exc()


async def run_nightmode_notifications():
    now = datetime.now()
    rows = await managers.chat_settings.get_by_field(setting="nightmode", pos=True)
    for chat_id, _ in rows:
        value = await managers.chat_settings.get(chat_id, "nightmode", "value2")
        if value is None:
            continue
        start_str, end_str = value.split("-")
        start = datetime.strptime(start_str, "%H:%M").replace(year=2024)
        end = datetime.strptime(end_str, "%H:%M").replace(year=2024)
        if now.hour == start.hour and now.minute == start.minute:
            await send_message(
                chat_id + 2000000000,
                await messages.nightmode_start(
                    start.strftime("%H:%M"), end.strftime("%H:%M")
                ),
            )
        elif now.hour == end.hour and now.minute == end.minute:
            await send_message(chat_id + 2000000000, await messages.nightmode_end())


async def mathgiveaway(conn: asyncpg.Connection):
    now = datetime.now()
    if now.hour in (9, 21) and now.minute < 15:
        math, ans = generate_hard_problem()
        level, xp = 2, random.randint(1000, 1200)
    elif now.hour in range(0, 23, 2) and now.minute < 15:
        math, ans = generate_medium_problem()
        level, xp = 1, random.randint(500, 800)
    else:
        math, ans = generate_easy_problem()
        level, xp = 0, random.randint(200, 400)

    old = [
        row[0]
        for row in await conn.fetch(
            "SELECT cmid FROM mathgiveaway WHERE finished = false"
        )
    ]
    if old:
        await delete_messages(old, settings.service.mathgiveaways_to)
    await conn.execute("UPDATE mathgiveaway SET finished = true WHERE finished = false")

    for attempt in range(3):
        cmid = await send_message(
            settings.service.mathgiveaways_to + 2000000000,
            await messages.math_problem(math, level, xp),
        )
        if isinstance(cmid, list):
            break
        logger.warning(f"mathgiveaway send_message failed, attempt {attempt + 1}/3")
        await asyncio.sleep(1)
    else:
        logger.error("mathgiveaway failed to send message after 3 attempts")
        return

    cmid = cmid[0].conversation_message_id
    await conn.execute(
        "INSERT INTO mathgiveaway (math, level, cmid, xp, ans, winner, finished) VALUES ($1, $2, $3, $4, $5, NULL, false)",
        math,
        level,
        cmid,
        xp,
        ans,
    )


async def everyday(conn: asyncpg.Connection):
    for attempt in range(12):
        try:
            await conn.execute("UPDATE shop SET limits='[0, 0, 0, 0, 0]'")
            await managers.xp.nullify_xp_limit()
            await managers.chat_user_cmids.clear()
        except asyncpg.exceptions.DeadlockDetectedError:
            if attempt == 12 - 1:
                raise
            await asyncio.sleep(0.1 * min(2 ** attempt, 256))


async def drop_event_tasks():
    await managers.event.drop_tasks()


async def new_tg_giveaway(conn: asyncpg.Connection):
    msg = await tgbot.send_message(
        chat_id=settings.telegram.public_chat_id,
        message_thread_id=settings.telegram.public_giveaway_thread_id,
        reply_markup=tgkeyboard.joingiveaway(0),
        text=f"<b>🎁 Ежедневный конкурс на <code>999</code> опыта для <code>3</code> участников Telegram канала."
        f"</b>\n\n<blockquote><b>💬 Для участия в конкурсе вы должны быть подписаны на данный канал, а так же "
        f'привязать профиль ВК для получения приза (<a href="https://t.me/{settings.telegram.bot_username}?start=0">'
        f'клик</a>). После выполнения всех условий нажмите кнопку "</b>Хочу участвовать<b>".</b></blockquote>'
        f"\n\n<b>🕒 Окончание конкурса будет завтра в <code>09:00</code> по МСК</b>",
    )
    await conn.execute("insert into tggiveaways (mid) values ($1)", msg.message_id)


async def end_tg_giveaway(conn: asyncpg.Connection):
    winners = []
    mid = await conn.fetchval("select mid from tggiveaways")
    users = await conn.fetch("select tgid from tggiveawayusers")
    await conn.execute("delete from tggiveaways")
    await conn.execute("delete from tggiveawayusers")
    random.shuffle(users)
    for i in users:
        user = await conn.fetchrow("select vkid, tgid from tglink where tgid=$1", i[0])
        if user and not await getULvlBanned(user[0]):
            winners.append(user)
            if len(winners) == 3:
                break
    for i in winners:
        await add_user_xp(i[0], 999, False)
        try:
            await tgbot.send_message(
                chat_id=i[1],
                text="<b>🎁 Поздравляем, вы выиграли 999 опыта в последнем конкурсе.</b>",
            )
        except Exception:
            pass
    emoji = ["🥇", "🥈", "🥉"]
    text = "<b>🏆 Итоги ежедневного конкурса</b>\n\n"
    if winners:
        text += "<blockquote><b>"
        for k, i in enumerate(winners):
            text += f'{emoji[k]} Победитель: <a href="https://vk.com/id{i[0]}">{await get_user_name(i[0])}</a>'
            if k - 1 != len(winners):
                text += "\n"
        text += (
            "</b></blockquote>\n\n<b>💬 Призы в виде <code>999</code> опыта были начислены победителям на их "
            "аккаунтах. Следующий конкурс в <code>10:00</code> МСК.</b>"
        )
    else:
        text += "<b>⚠️ Никто не участвовал в этом конкурсе.</b>"
    await tgbot.edit_message_text(
        chat_id=settings.telegram.public_chat_id, message_id=mid, text=text
    )


def add_jobs(scheduler):
    logger.info("Loading scheduler tasks...")

    # timeouts are calculated based on task execution intervals to prevent overlapping
    scheduler.add_job(
        schedule(run_notifications, timeout=180),
        CronTrigger.from_crontab("1/3 * * * *"),
        id="run_notifications",
    )
    scheduler.add_job(
        schedule(run_nightmode_notifications, use_db=False, timeout=180),
        CronTrigger.from_crontab("*/1 * * * *"),
        id="run_nightmode_notifications",
    )
    scheduler.add_job(
        schedule(everyminute, timeout=60),
        CronTrigger.from_crontab("*/1 * * * *"),
        id="everyminute",
    )

    scheduler.add_job(
        schedule(every10min, timeout=600),
        CronTrigger.from_crontab("*/10 * * * *"),
        id="every10min",
    )

    scheduler.add_job(
        schedule(backup, use_db=False, timeout=None),
        CronTrigger.from_crontab("0 6,18 * * *"),
        id="backup",
    )

    scheduler.add_job(
        schedule(updateChats, timeout=10800),
        CronTrigger.from_crontab("0 0/3 * * *"),
        id="updateChats",
    )
    scheduler.add_job(
        schedule(updateGroups, timeout=10800),
        CronTrigger.from_crontab("0 1/3 * * *"),
        id="updateGroups",
    )
    scheduler.add_job(
        schedule(updateUsers, timeout=10800),
        CronTrigger.from_crontab("0 2/3 * * *"),
        id="updateUsers",
    )

    scheduler.add_job(
        schedule(mathgiveaway, timeout=900),
        CronTrigger.from_crontab("*/15 * * * *"),
        id="mathgiveaway",
    )

    scheduler.add_job(
        schedule(everyday, timeout=86400),
        CronTrigger.from_crontab("0 0 * * *"),
        id="everyday",
    )

    scheduler.add_job(
        schedule(drop_event_tasks, timeout=86400, use_db=False),
        CronTrigger.from_crontab("0 5 * * *"),
        id="drop_event_tasks",
    )

    scheduler.add_job(
        schedule(new_tg_giveaway, timeout=86400),
        CronTrigger.from_crontab("0 10 * * *"),
        id="new_tg_giveaway",
    )
    scheduler.add_job(
        schedule(end_tg_giveaway, timeout=86400),
        CronTrigger.from_crontab("0 9 * * *"),
        id="end_tg_giveaway",
    )

    logger.info(f"Loaded {len(scheduler.get_jobs())} scheduler jobs")
