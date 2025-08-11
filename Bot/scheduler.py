import asyncio
import os
import random
import string
import subprocess
import time
import traceback
from datetime import datetime

import aiocron
import yadisk
from loguru import logger

import keyboard
import messages
from Bot.tgbot import tgbot
from Bot.utils import (
    beautifyNumber,
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
    DAILY_TO,
    DATABASE,
    DEV_TGID,
    GROUP_ID,
    MATHGIVEAWAYS_TO,
    PASSWORD,
    PATH,
    PHOTO_NOT_FOUND,
    STATUSCHECKER_CMD,
    STATUSCHECKER_TO,
    TG_BACKUP_THREAD_ID,
    TG_CHAT_ID,
    USER,
    YANDEX_TOKEN,
    api,
    implicitapi,
    vk_api_session,
)
from db import schedulerpool as pool

task_locks = {
    "backup": asyncio.Lock(),
    "updateInfo": asyncio.Lock(),
    "reboot": asyncio.Lock(),
    "every10min": asyncio.Lock(),
    "everyminute": asyncio.Lock(),
    "run_notifications": asyncio.Lock(),
    "run_nightmode_notifications": asyncio.Lock(),
    "botstatuschecker": asyncio.Lock(),
    "mathgiveaway": asyncio.Lock(),
    "everyday": asyncio.Lock(),
}


async def with_lock(name, func, use_db=True):
    lock = task_locks[name]
    if lock.locked():
        return
    async with lock:
        try:
            if use_db:
                async with (await pool()).acquire() as conn:
                    await func(conn)
            else:
                await func(None)
        except Exception:
            traceback.print_exc()
            await sendMessage(
                DAILY_TO + 2000000000,
                f"e from schedule {name}:\n" + traceback.format_exc(),
            )
            traceback.print_exc()
            await sendMessage(
                DAILY_TO + 2000000000,
                f"e from schedule {name}:\n" + traceback.format_exc(),
            )


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
    ts_cutoff = time.time() - 43200
    allusers = beautifyNumber(await conn.fetchval("SELECT COUNT(*) FROM allusers"))
    allchats = beautifyNumber(await conn.fetchval("SELECT COUNT(*) FROM allchats"))
    await implicitapi.status.set(
        group_id=GROUP_ID,
        text=f"👥 Пользователей: {allusers} | 💬 Бесед: {allchats}",
    )

    for chunk in chunks(await conn.fetch("SELECT uid FROM usernames"), 999):
        try:
            names = await api.users.get(user_ids=[row[0] for row in chunk])
            await conn.executemany(
                "UPDATE usernames SET name = $1 WHERE uid = $2",
                [(f"{name.first_name} {name.last_name}", name.id) for name in names],
            )
        except Exception:
            pass

    for chunk in chunks(await conn.fetch("SELECT chat_id FROM chatnames"), 99):
        try:
            chats = await api.messages.get_conversations_by_id(
                peer_ids=[2000000000 + row[0] for row in chunk]
            )
            await conn.executemany(
                "UPDATE chatnames SET name = $1 WHERE chat_id = $2",
                [
                    (chat.chat_settings.title, chat.peer.id - 2000000000)
                    for chat in chats.items
                ],
            )
        except Exception:
            pass

    for chunk in chunks(await conn.fetch("SELECT group_id FROM groupnames"), 499):
        try:
            groups = await api.groups.get_by_id(group_ids=[row[0] for row in chunk])
            await conn.executemany(
                "UPDATE groupnames SET name = $1 WHERE group_id = $2",
                [(g.name, -abs(g.id)) for g in groups.groups],
            )
        except Exception:
            pass

    recent_updates = [
        row[0]
        for row in await conn.fetch(
            "SELECT chat_id FROM publicchatssettings WHERE last_update > $1",
            ts_cutoff,
        )
    ]
    for row in await conn.fetch(
        "SELECT chat_id FROM publicchats WHERE isopen = true AND NOT chat_id = ANY($1)",
        recent_updates,
    ):
        chat_id = row[0]
        try:
            link = vk_api_session.method(
                "messages.getInviteLink",
                {"peer_id": 2000000000 + chat_id, "group_id": GROUP_ID},
            )["link"]
            vkchat = vk_api_session.method(
                "messages.getConversationsById", {"peer_ids": 2000000000 + chat_id}
            )
            if "items" not in vkchat or not vkchat["items"]:
                continue
            vkchat = vkchat["items"][0]["chat_settings"]
            photo = (
                vkchat.get("photo", {}).get("photo_200")
                or vkchat.get("photo", {}).get("photo_100")
                or vkchat.get("photo", {}).get("photo_50")
                or PHOTO_NOT_FOUND
            )
            if not await conn.fetchval(
                "UPDATE publicchatssettings SET link = $1, photo = $2, name = $3, members = $4, last_update = $5 "
                "WHERE chat_id = $6 RETURNING 1",
                link,
                photo,
                vkchat["title"],
                vkchat["members_count"],
                time.time(),
                chat_id,
            ):
                await conn.execute(
                    "INSERT INTO publicchatssettings (chat_id, link, photo, name, members, last_update) "
                    "VALUES ($1, $2, $3, $4, $5, $6)",
                    chat_id,
                    link,
                    photo,
                    vkchat["title"],
                    vkchat["members_count"],
                    time.time(),
                )
        except Exception:
            await conn.execute(
                "UPDATE publicchats SET isopen = false WHERE chat_id = $1", chat_id
            )
        await asyncio.sleep(0.2)


async def reboot(conn):
    await conn.execute(
        "INSERT INTO reboots (chat_id, time, sended) VALUES ($1, $2, false)",
        DAILY_TO + 2000000000,
        time.time(),
    )
    await (await pool()).release(conn)
    await (await pool()).close()
    os.system("sudo reboot")


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


async def botstatuschecker():
    await implicitapi.messages.send(
        random_id=0,
        peer_ids=STATUSCHECKER_TO + 2000000000,
        message=STATUSCHECKER_CMD,
    )
    await asyncio.sleep(300)
    history = await implicitapi.messages.get_history(
        count=1, peer_id=STATUSCHECKER_TO + 2000000000
    )
    if history.items[0].from_id != -GROUP_ID:
        await tgbot.send_message(chat_id=DEV_TGID, text="Bot status: down...")


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
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    logger.info("loading tasks")

    aiocron.crontab(
        "*/1 * * * *",
        func=lambda: with_lock("run_notifications", run_notifications),
        loop=loop,
    )
    aiocron.crontab(
        "*/1 * * * *",
        func=lambda: with_lock(
            "run_nightmode_notifications", run_nightmode_notifications
        ),
        loop=loop,
    )
    aiocron.crontab(
        "*/1 * * * *", func=lambda: with_lock("everyminute", everyminute), loop=loop
    )
    aiocron.crontab(
        "*/10 * * * *", func=lambda: with_lock("every10min", every10min), loop=loop
    )
    aiocron.crontab(
        "0 6/12 * * *",
        func=lambda: with_lock("backup", backup, use_db=False),
        loop=loop,
    )
    aiocron.crontab(
        "0 1/3 * * *", func=lambda: with_lock("updateInfo", updateInfo), loop=loop
    )
    # aiocron.crontab("*/15 * * * *", func=lambda: with_lock("botstatuschecker", botstatuschecker), loop=loop)
    aiocron.crontab(
        "*/15 * * * *", func=lambda: with_lock("mathgiveaway", mathgiveaway), loop=loop
    )
    # aiocron.crontab("50 23 * * *", func=lambda: with_lock("reboot", reboot), loop=loop)
    aiocron.crontab(
        "0 0 * * *", func=lambda: with_lock("everyday", everyday), loop=loop
    )
