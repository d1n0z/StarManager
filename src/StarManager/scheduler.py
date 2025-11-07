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
        start = time.time()
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
            elapsed = time.time() - start
            if elapsed > 60:
                logger.warning(f"Task {func.__name__} took {elapsed:.1f}s")
            scheduler_monitor.mark_run(func.__name__)
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
    from StarManager.backup_service import backup_service
    await backup_service.create_backup()


async def updateUsers(conn):  # TODO: optimize
    user_rows = await conn.fetch("select uid from usernames")
    for i in range(0, len(user_rows), 25):
        batch = [r[0] for r in user_rows[i : i + 25]]
        try:
            users = await api.users.get(user_ids=batch, fields=["domain"])  # type: ignore
            updates = []
            for u in users:
                full_name = f"{u.first_name} {u.last_name}" if u.first_name and u.last_name else "Unknown"
                domain = u.domain or f"id{u.id}"
                updates.append((full_name, domain, u.id))
            await conn.executemany(
                "update usernames set name = $1, domain = $2 where uid = $3", updates
            )
        except Exception:
            logger.exception("Users update exception:")


async def updateChats(conn):
    chatnames_ids = [i[0] for i in await conn.fetch("select chat_id from chatnames")]
    publicchats_ids = [
        i[0] for i in await conn.fetch("select chat_id from publicchats")
    ]
    total_chat_ids = list(set(chatnames_ids + publicchats_ids))
    if not total_chat_ids:
        return

    updates_chatnames = []
    updates_publicchats = []

    for chat_ids in chunks(total_chat_ids, 100) if total_chat_ids else []:
        peer_ids = [2000000000 + cid for cid in chat_ids]

        try:
            conv = await api.messages.get_conversations_by_id(peer_ids=peer_ids)
        except Exception:
            logger.exception("getConversationsById failed:")
            continue

        members_cache = {}

        for item in getattr(conv, "items", []):
            try:
                if not item.peer or not item.chat_settings:
                    continue

                chat_id = item.peer.id - 2000000000
                title = item.chat_settings.title
                members_count = item.chat_settings.members_count

                if not members_count:
                    await asyncio.sleep(0.34)
                    try:
                        members = await api.messages.get_conversation_members(
                            peer_id=item.peer.id
                        )
                        members_count = len(members.items)
                        members_cache[chat_id] = members_count
                    except Exception:
                        members_count = None

                updates_chatnames.append((title, chat_id))
                if members_count is not None:
                    updates_publicchats.append((members_count, chat_id))

            except Exception:
                logger.exception(f"Error processing chat item {item}")
                continue

        missing = [
            cid
            for cid in chat_ids
            if cid not in members_cache
            and cid not in [u[1] for u in updates_publicchats]
        ]
        for chat_id in missing:
            try:
                members = await api.messages.get_conversation_members(
                    peer_id=2000000000 + chat_id
                )
                updates_publicchats.append((len(members.items), chat_id))
            except Exception:
                pass

    if updates_chatnames:
        await conn.executemany(
            "update chatnames set name = $1 where chat_id = $2", updates_chatnames
        )

    if updates_publicchats:
        await conn.executemany(
            "update publicchats set members_count = $1 where chat_id = $2",
            updates_publicchats,
        )


async def updateGroups(conn):  # TODO: optimize
    group_rows = await conn.fetch("select group_id from groupnames")
    for i in range(0, len(group_rows), 500):
        batch = [r[0] for r in group_rows[i : i + 500]]
        code = f"""
        var grp = API.groups.getById({{"group_ids": "{",".join(map(str, map(abs, batch)))}"}});
        return grp;
        """
        try:
            result = await api.execute(code)
            updates = []
            for g in result["groups"]:
                gid = -abs(g["id"])
                updates.append((g["name"], gid))
            await conn.executemany(
                "update groupnames set name = $1 where group_id = $2", updates
            )
        except Exception:
            logger.exception("Groups update exception:")


async def every10min(conn):
    await asyncio.to_thread(
        os.system,
        rf"find {settings.service.path}src/StarManager/core/media/temp/ -mtime +1 -exec rm {{}} \;"
    )
    now = time.time()
    await conn.execute('DELETE FROM prempromo WHERE "end" < $1', now)
    await conn.execute("DELETE FROM premium WHERE time < $1", now)
    expired = await conn.fetch(
        "SELECT uid, cmid FROM premiumexpirenotified WHERE date < $1",
        now - 86400 * 2,
    )
    if expired:
        await asyncio.gather(*(delete_messages(cmid, uid) for uid, cmid in expired), return_exceptions=True)
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
                group_id=settings.vk.group_id, user_ids=[row[0] for row in chunk]
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
            return_exceptions=True
        )
        await conn.execute("DELETE FROM todelete WHERE delete_at < $1", now)


async def run_notifications(conn):
    now = int(time.time())
    rows = await conn.fetch("select id, chat_id, tag, every, time, name, text from notifications where status = 1 and every != -1 and time < $1 and not exists (select 1 from blocked where uid = notifications.chat_id and type = 'chat')", now)
    for row in rows:
        id_, chat_id, tag, every, ttime, name, text = row
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
                if not await send_message(
                    chat_id + 2000000000, await messages.send_notification(text, call), disable_mentions=False
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
            await send_message(
                chat_id + 2000000000,
                await messages.nightmode_start(
                    start.strftime("%H:%M"), end.strftime("%H:%M")
                ),
            )
        elif now.hour == end.hour and now.minute == end.minute:
            await send_message(chat_id + 2000000000, await messages.nightmode_end())


async def mathgiveaway(conn):
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


async def everyday(conn):
    await conn.execute("UPDATE shop SET limits='[0, 0, 0, 0, 0]'")
    await managers.xp.nullify_xp_limit()
    await managers.chat_user_cmids.clear()


async def new_tg_giveaway(conn):
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


async def end_tg_giveaway(conn):
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

    scheduler.add_job(
        schedule(run_notifications), CronTrigger.from_crontab("1/3 * * * *"), id="run_notifications"
    )
    scheduler.add_job(
        schedule(run_nightmode_notifications), CronTrigger.from_crontab("0/3 * * * *"), id="run_nightmode_notifications"
    )
    scheduler.add_job(schedule(everyminute), CronTrigger.from_crontab("*/1 * * * *"), id="everyminute")

    scheduler.add_job(schedule(every10min), CronTrigger.from_crontab("*/10 * * * *"), id="every10min")

    scheduler.add_job(
        schedule(backup, use_db=False, timeout=None), CronTrigger.from_crontab("0 6,18 * * *"), id="backup"
    )

    scheduler.add_job(schedule(updateChats, timeout=600), CronTrigger.from_crontab("0 0/3 * * *"), id="updateChats")
    scheduler.add_job(schedule(updateGroups, timeout=600), CronTrigger.from_crontab("0 1/3 * * *"), id="updateGroups")
    scheduler.add_job(schedule(updateUsers, timeout=600), CronTrigger.from_crontab("0 2/3 * * *"), id="updateUsers")

    scheduler.add_job(schedule(mathgiveaway), CronTrigger.from_crontab("*/15 * * * *"), id="mathgiveaway")

    scheduler.add_job(schedule(everyday), CronTrigger.from_crontab("0 0 * * *"), id="everyday")

    scheduler.add_job(schedule(new_tg_giveaway), CronTrigger.from_crontab("0 10 * * *"), id="new_tg_giveaway")
    scheduler.add_job(schedule(end_tg_giveaway), CronTrigger.from_crontab("0 9 * * *"), id="end_tg_giveaway")
    
    logger.info(f"Loaded {len(scheduler.get_jobs())} scheduler jobs")
