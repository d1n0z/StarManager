import asyncio
import os
import statistics
import time
import traceback
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.checkers import getUInfBanned
from StarManager.vkbot.rules import SearchCMD
from StarManager.scheduler import backup
from StarManager.core.utils import (
    add_user_coins,
    get_user_name,
    search_id_in_message,
    get_user_nickname,
    send_message,
    add_user_xp,
    get_chat_name,
    set_user_access_level,
    point_words,
    chunks,
    get_user_rep_banned,
    messagereply,
    kick_user,
)
from StarManager.core.config import api, settings
from StarManager.core.db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD("getdev"))
async def getdev_handler(message: Message):
    uid = message.from_id
    if uid in settings.service.devs:
        await set_user_access_level(uid, message.peer_id - 2000000000, 8)


@bl.chat_message(SearchCMD("backup"))
async def backup_handler(message: Message):
    await backup()
    await messagereply(message, "💚 Completed.")


@bl.chat_message(SearchCMD("msg"))
async def msg(message: Message):
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(message, await messages.msg_hint())
    devmsg = " ".join(data[1:])
    msg = await messages.msg(devmsg)
    k = 0
    async with (await pool()).acquire() as conn:
        chats = await conn.fetch("select chat_id from allchats")
    print(len(chats))
    for i in chunks(chats, 2500):
        try:
            code = ""
            for y in chunks(i, 100):
                code += (
                    'API.await messages.send({"random_id": 0, "peer_ids": ['
                    + ",".join(str(o[0]) for o in y)
                    + '], "message": "'
                    + f"{msg}"
                    + '"});'
                )
            await api.execute(code=code)
            k += len(i)
            print(f"sent {k}/{len(chats)}")
            await asyncio.sleep(1)
        except Exception:
            traceback.print_exc()
    msg = f"done {k}/{len(chats)}"
    print(msg)
    await messagereply(message, msg)


@bl.chat_message(SearchCMD("addblack"))
async def addblack(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if id == 0:
        return await messagereply(message, await messages.addblack_hint())
    if id == uid:
        return await messagereply(message, await messages.addblack_myself())
    if id < 0:
        return await messagereply(message, await messages.id_group())
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into blacklist (uid) values ($1) on conflict (uid) do nothing", id
        )
    dev_name = await get_user_name(uid)
    dev_nickname = await get_user_nickname(uid, chat_id)
    await messagereply(
        message,
        await messages.addblack(
            uid,
            dev_name,
            dev_nickname,
            id,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
        ),
    )
    await send_message(id, await messages.blacked(uid, dev_name, dev_nickname))


@bl.chat_message(SearchCMD("delblack"))
async def delblack(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if id == 0:
        return await messagereply(message, await messages.delblack_hint())
    if id == uid:
        return await messagereply(message, await messages.delblack_myself())
    if id < 0:
        return await messagereply(message, await messages.id_group())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "delete from blacklist where uid=$1 returning 1", id
        ):
            return await messagereply(
                message,
                await messages.delblack_no_user(
                    id, await get_user_name(id), await get_user_nickname(id, chat_id)
                ),
            )
    dev_name = await get_user_name(uid)
    dev_nickname = await get_user_nickname(uid, chat_id)
    await messagereply(
        message,
        await messages.delblack(
            uid,
            dev_name,
            dev_nickname,
            id,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
        ),
    )
    await send_message(id, await messages.delblacked(uid, dev_name, dev_nickname))


@bl.chat_message(SearchCMD("blacklist"))
async def blacklist(message: Message):
    users = {}
    async with (await pool()).acquire() as conn:
        blc = await conn.fetch("select uid from blacklist")
    for user in blc:
        users[await get_user_name(user[0])] = user[0]
    msg = f"⚛ Список пользователей в ЧС бота (Всего : {len(list(users))})\n\n"
    for k, i in users.items():
        msg += f"➖ {i} : | [id{i}|{k}]\n"
    await messagereply(message, msg)


@bl.chat_message(SearchCMD("setstatus"))
async def setstatus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    data = message.text.split()
    if id == 0 or not data[2].isdigit():
        return await messagereply(message, await messages.setstatus_hint())
    if id < 0:
        return await messagereply(message, await messages.id_group())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update premium set time = $1 where uid=$2 returning 1",
            time.time() + int(data[2]) * 86400,
            id,
        ):
            await conn.execute(
                "insert into premium (uid, time) values ($1, $2)",
                id,
                time.time() + int(data[2]) * 86400,
            )

    dev_name = await get_user_name(uid)
    await messagereply(
        message,
        await messages.setstatus(
            uid,
            dev_name,
            await get_user_nickname(uid, chat_id),
            id,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
        ),
    )
    await send_message(
        id,
        await messages.ugiveStatus(
            id,
            await get_user_nickname(id, chat_id),
            await get_user_name(id),
            uid,
            await get_user_nickname(uid, chat_id),
            dev_name,
            data[2],
        ),
    )


@bl.chat_message(SearchCMD("delstatus"))
async def delstatus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if id == 0:
        return await messagereply(message, await messages.delstatus_hint())
    if id < 0:
        return await messagereply(message, await messages.id_group())
    async with (await pool()).acquire() as conn:
        await conn.execute("delete from premium where uid=$1", id)

    dev_name = await get_user_name(uid)
    await messagereply(
        message,
        await messages.delstatus(
            uid,
            dev_name,
            await get_user_nickname(uid, chat_id),
            id,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
        ),
    )
    await send_message(id, await messages.udelStatus(uid, dev_name))


@bl.chat_message(SearchCMD("statuslist"))
async def statuslist(message: Message):
    async with (await pool()).acquire() as conn:
        prem = await conn.fetch("select uid, time from premium")
    await messagereply(
        message,
        await messages.statuslist(prem),
        keyboard=keyboard.statuslist(message.from_id, 0, len(prem)),
    )


@bl.chat_message(SearchCMD("setprem"))
async def setprem(message: Message):
    uid = message.from_id
    chat_id = await search_id_in_message(message.text, message.reply_message)
    if chat_id <= 0:
        return await messagereply(message, await messages.setprem_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update publicchats set premium = true where chat_id=$1 returning 1",
            chat_id,
        ):
            await conn.execute(
                "insert into publicchats (chat_id, premium, isopen) values ($1, true, false)",
                chat_id,
            )

    await messagereply(message, await messages.setprem(chat_id))
    await send_message(
        message.peer_id, await messages.premchat(uid, await get_user_name(uid))
    )


@bl.chat_message(SearchCMD("delprem"))
async def delprem(message: Message):
    chat_id = await search_id_in_message(message.text, message.reply_message)
    if chat_id <= 0:
        return await messagereply(message, await messages.delprem_hint())
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "update publicchats set premium = false where chat_id=$1", chat_id
        )
    await messagereply(message, await messages.delprem(chat_id))


@bl.chat_message(SearchCMD("premlist"))
async def permlist(message: Message):
    async with (await pool()).acquire() as conn:
        prem = await conn.fetch("select chat_id from publicchats where premium=true")
    await messagereply(message, await messages.premlist(prem))


@bl.chat_message(SearchCMD("givexp"))
async def givexp(message: Message):
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(message, "🔶 Пользователь не найден")
    data = message.text.split()
    await add_user_xp(id, int(data[2]))
    await messagereply(
        message,
        await messages.givexp(
            uid, await get_user_name(uid), id, await get_user_name(id), data[2]
        ),
    )


@bl.chat_message(SearchCMD("givecoins"))
async def givecoins(message: Message):
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(message, "🔶 Пользователь не найден")
    data = message.text.split()
    await add_user_coins(id, int(data[2]))
    await messagereply(
        message,
        await messages.givecoins(
            uid, await get_user_name(uid), id, await get_user_name(id), data[2]
        ),
    )


@bl.chat_message(SearchCMD("resetlvl"))
async def resetlvl(message: Message):
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(message, "🔶 Пользователь не найден")
    async with (await pool()).acquire() as conn:
        await conn.execute("update xp set xp=0, lvl=0, league=1 where uid=$1", id)
    u_name = await get_user_name(id)
    msgsent = await messages.resetlvlcomplete(id, u_name)
    if (
        await send_message(peer_ids=id, msg=await messages.resetlvl(id, u_name))
        is False
    ):
        msgsent += "\n❗ Пользователю не удалось отправить сообщение"
    await messagereply(message, msgsent)


@bl.chat_message(SearchCMD("block"))
async def block(message: Message):
    data = message.text.lower().split()
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if len(data) < 3 or data[1] not in ["chat", "user"] or not id or id < 0:
        return await messagereply(message, await messages.block_hint())
    reason = " ".join(data[3:]) or None
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "select exists(select 1 from blocked where uid=$1 and type=$2)", id, data[1]
        ):
            await conn.execute(
                "insert into blocked (uid, type, reason) values ($1, $2, $3)",
                id,
                data[1],
                reason,
            )
            if data[1] != "chat":
                await conn.execute("delete from xp where uid=$1", id)
                await conn.execute("delete from premium where uid=$1", id)
                chats = (
                    set(
                        i[0]
                        for i in await conn.fetch(
                            "select chat_id from userjoineddate where uid=$1", id
                        )
                    )
                    or set()
                )
                chats.update(
                    i[0]
                    for i in await conn.fetch(
                        "select chat_id from accesslvl where uid=$1", id
                    )
                )
                chats.update(
                    i[0]
                    for i in await conn.fetch(
                        "select chat_id from nickname where uid=$1", id
                    )
                )
                chats.update(
                    i[0]
                    for i in await conn.fetch(
                        "select chat_id from lastmessagedate where uid=$1", id
                    )
                )
    if data[1] == "chat":
        await send_message(
            id + 2000000000,
            await messages.block_chatblocked(id, reason),
            keyboard.block_chatblocked(),
        )
        await api.messages.remove_chat_user(id, member_id=-settings.vk.group_id)
    else:
        await send_message(
            id,
            await messages.block_userblocked(id, reason),
            keyboard.block_chatblocked(),
        )
        for i in chats:
            if await kick_user(id, i):
                await send_message(
                    i + 2000000000,
                    await messages.block_blockeduserinvite(
                        id, await get_user_name(id), reason
                    ),
                )
            await asyncio.sleep(0.3)
    await messagereply(message, await messages.block())


@bl.chat_message(SearchCMD("unblock"))
async def unblock(message: Message):
    data = message.text.lower().split()
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if len(data) != 3 or data[1] not in ["chat", "user"] or not id:
        return await messagereply(message, await messages.unblock_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "delete from blocked where uid=$1 and type=$2 returning 1", id, data[1]
        ):
            return await messagereply(message, await messages.unblock_noban())
    if data[1] == "chat":
        await send_message(id + 2000000000, await messages.block_chatunblocked(id))
    await messagereply(message, await messages.unblock())


@bl.chat_message(SearchCMD("blocklist"))
async def blocklist(message: Message):
    async with (await pool()).acquire() as conn:
        inf = await conn.fetch("select uid, reason from blocked where type='user'")
    msg = f"⚛ Список пользователей в блокировке бота (Всего : {len(inf)})\n\n"
    for user in inf:
        msg += (
            f"➖ [id{user[0]}|{await get_user_name(user[0])}]"
            + (f" | {user[1]}" if user[1] else "")
            + "\n"
        )
    await messagereply(message, msg, keyboard=keyboard.blocklist(message.from_id))


@bl.chat_message(SearchCMD("cmdcount"))
async def cmdcount(message: Message):
    async with (await pool()).acquire() as conn:
        cmdsraw = await conn.fetch(
            "select cmd, timestart, timeend from commandsstatistics where timeend is not null"
        )
    cmds = {}
    for i in cmdsraw:
        if i[0] not in cmds:
            cmds[i[0]] = [i[2].timestamp() - i[1].timestamp()]
        else:
            cmds[i[0]].append(i[2].timestamp() - i[1].timestamp())
    msg = ""
    for i in cmds.keys():
        msg += (
            f"{i}: {statistics.mean(cmds[i])} секунд | использован {len(cmds[i])} раз\n"
        )
    await messagereply(message, disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD("msgsaverage"))
async def msgsaverage(message: Message):
    async with (await pool()).acquire() as conn:
        msts = await conn.fetch(
            "select timestart, timeend from messagesstatistics where timeend is not null"
        )
    msgs = [i[1].timestamp() - i[0].timestamp() for i in msts]
    await messagereply(
        message,
        disable_mentions=1,
        message=f"Среднее время обработки - {statistics.mean(msgs)} секунд",
    )


@bl.chat_message(SearchCMD("msgscount"))
async def msgscount(message: Message):
    now = datetime.now()
    async with (await pool()).acquire() as conn:
        msgs5minutes = await conn.fetchval(
            "select count(*) as c from messagesstatistics where timeend is not null and "
            "extract(minute from timestart)>=$1 and extract(hour from timestart)=$2 and "
            "extract(day from timestart)=$3 and extract(month from timestart)=$4 and "
            "extract(year from timestart)=$5",
            now.minute - 5,
            now.hour,
            now.day,
            now.month,
            now.year,
        )
        msgsminute = await conn.fetchval(
            "select count(*) as c from messagesstatistics where timeend is not null and "
            "extract(minute from timestart)=$1 and extract(hour from timestart)=$2 and "
            "extract(day from timestart)=$3 and extract(month from timestart)=$4 and "
            "extract(year from timestart)=$5",
            now.minute,
            now.hour,
            now.day,
            now.month,
            now.year,
        )
        msgshour = await conn.fetchval(
            "select count(*) as c from messagesstatistics where timeend is not null and "
            "extract(hour from timestart)=$1 and extract(day from timestart)=$2 and "
            "extract(month from timestart)=$3 and extract(year from timestart)=$4",
            now.hour,
            now.day,
            now.month,
            now.year,
        )
        msgslasthour = await conn.fetchval(
            "select count(*) as c from messagesstatistics where timeend is not null and "
            "extract(hour from timestart)=$1 and extract(day from timestart)=$2 and "
            "extract(month from timestart)=$3 and extract(year from timestart)=$4",
            now.hour - 1,
            now.day,
            now.month,
            now.year,
        )
        msgsday = await conn.fetchval(
            "select count(*) as c from messagesstatistics where timeend is not null and "
            "extract(day from timestart)=$1 and extract(month from timestart)=$2 and "
            "extract(year from timestart)=$3",
            now.day,
            now.month,
            now.year,
        )
        msgslastday = await conn.fetchval(
            "select count(*) as c from messagesstatistics where timeend is not null and "
            "extract(day from timestart)=$1 and extract(month from timestart)=$2 and "
            "extract(year from timestart)=$3",
            now.day - 1,
            now.month,
            now.year,
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=f"{msgslastday} сообщений за вчера\n"
        f"{msgslasthour} сообщений за прошлый час\n"
        f"{msgs5minutes} сообщений за последние 5 минут\n"
        f"{msgsday} сообщений за сегодня\n"
        f"{msgshour} сообщений за этот час\n"
        f"{msgsminute} сообщений за эту минуту",
    )


@bl.chat_message(SearchCMD("getlink"))
async def getlink(message: Message):
    data = message.text.lower().split()
    if len(data) != 2 or not data[1].isdigit():
        return await messagereply(message, "/getlink chat_id")
    try:
        await messagereply(
            message,
            (
                await api.messages.get_invite_link(
                    peer_id=int(data[1]) + 2000000000,
                    reset=False,
                    group_id=settings.vk.group_id,
                )
            ).link,
        )
    except Exception:
        await messagereply(message, "❌ Невозможно сгенерировать ссылку")


@bl.chat_message(SearchCMD("reboot"))
async def reboot(message: Message):
    if len(data := message.text.split()) == 2:
        await messagereply(
            message,
            f"⌛ Перезагрузка произойдет через {point_words(int(data[1]), ('минуту', 'минуты', 'минут'))}.",
        )
        await asyncio.sleep(int(data[1]) * 60)
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into reboots (chat_id, time, sended) values ($1, $2, false)",
            message.chat_id,
            time.time(),
        )
    await messagereply(message, await messages.reboot())
    os.system(settings.service.path + "startup.sh")  # noqa


@bl.chat_message(SearchCMD("sudo"))
async def sudo(message: Message):
    if "reboot" in message.text:
        async with (await pool()).acquire() as conn:
            await conn.execute(
                "insert into reboots (chat_id, time, sended) values ($1, $2, false)",
                message.chat_id,
                time.time(),
            )
    await messagereply(
        message, os.popen(f"sudo {' '.join(message.text.split()[1:])}").read()
    )


@bl.chat_message(SearchCMD("getuserchats"))
async def getuserchats(message: Message):
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(message, "🔶 Пользователь не найден")
    limit = message.text.split()[-1]
    async with (await pool()).acquire() as conn:
        top = await conn.fetch(
            "select chat_id, messages from messages where uid=$1 order by messages desc limit "
            "$2",
            id,
            int(limit) if limit.isdigit() else 100,
        )
    msg = "✝ Беседы пользователя:\n"
    for i in top:
        if await getUInfBanned(id, i[0]):
            continue
        try:
            chu = len(
                (
                    await api.messages.get_conversation_members(
                        peer_id=2000000000 + i[0], group_id=settings.vk.group_id
                    )
                ).items
            )
        except Exception:
            chu = 0
        msg += f"➖ {i[0]} | M: {i[1]} | C: {chu} | N: {await get_chat_name(i[0])} \n"
    await messagereply(message, msg)


@bl.chat_message(SearchCMD("getchats"))
async def getchats(message: Message):
    limit = message.text.split()[-1]
    async with (await pool()).acquire() as conn:
        top = await conn.fetch(
            "select chat_id, messages from messages order by messages desc limit $1",
            int(limit) if limit.isdigit() else 100,
        )
    msg = "✝ Беседы:\n"
    for i in top:
        if str(i[0]) in msg or await getUInfBanned(0, i[0]):
            continue
        try:
            chu = len(
                (
                    await api.messages.get_conversation_members(
                        peer_id=2000000000 + i[0], group_id=settings.vk.group_id
                    )
                ).items
            )
        except Exception:
            chu = 0
        msg += f"➖ {i[0]} | M: {i[1]} | C: {chu} | N: {await get_chat_name(i[0])}\n"
    await messagereply(message, msg)


@bl.chat_message(SearchCMD("helpdev"))
async def helpdev(message: Message):
    await messagereply(message, await messages.helpdev())


@bl.chat_message(SearchCMD("gettransferhistory"))
@bl.chat_message(SearchCMD("gettransferhistoryto"))
@bl.chat_message(SearchCMD("gettransferhistoryfrom"))
async def gettransferhistory(message: Message):
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        await messagereply(message, "🔶 Пользователь не найден")
        return
    limit = message.text.split()[-1]
    limit = int(limit) if limit.isdigit() else 100
    async with (await pool()).acquire() as conn:
        if message.text.lower().split()[0][-2:] == "to":
            transfers = await conn.fetch(
                "select from_id, to_id, amount, com from transferhistory where to_id=$1 "
                "order by time desc limit $2",
                id,
                limit,
            )
        elif message.text.lower().split()[0][-4:] == "from":
            transfers = await conn.fetch(
                "select from_id, to_id, amount, com from transferhistory where from_id=$1 "
                "order by time desc limit $2",
                id,
                limit,
            )
        else:
            transfers = await conn.fetch(
                "select from_id, to_id, amount, com from transferhistory where from_id=$1 or to_id=$1"
                " order by time desc limit $2",
                id,
                limit,
            )
    msg = "✝ Общие трансферы пользователя:"
    for i in transfers:
        msg += (
            f"\n F: [id{i[0]}|{await get_user_name(i[0])}] | T: [id{i[1]}|{await get_user_name(i[1])}] | A: {i[2]} | C:"
            f" {not bool(i[3])}"
        )
    await messagereply(message, msg)


@bl.chat_message(SearchCMD("lvlban"))
async def lvlban(message: Message):
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await messagereply(message, await messages.lvlban_hint())
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into lvlbanned (uid) values ($1) on conflict (uid) do nothing", id
        )
    await messagereply(message, await messages.lvlban())


@bl.chat_message(SearchCMD("lvlunban"))
async def lvlunban(message: Message):
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await messagereply(message, await messages.lvlunban_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "delete from lvlbanned where uid=$1 returning 1", id
        ):
            return await messagereply(message, await messages.lvlunban_noban())
    await messagereply(message, await messages.lvlunban())


@bl.chat_message(SearchCMD("lvlbanlist"))
async def lvlbanlist(message: Message):
    async with (await pool()).acquire() as conn:
        lvlban = await conn.fetch("select uid from lvlbanned")
    msg = f"⚛ Список пользователей в lvlban бота (Всего : {len(lvlban)})\n\n"
    for user in lvlban:
        msg += f"➖ {user[0]} : | [id{user[0]}|{await get_user_name(user[0])}]\n"
    await messagereply(message, msg)


@bl.chat_message(SearchCMD("repban"))
async def repban(message: Message):
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await messagereply(message, await messages.repban_hint())
    if not await get_user_rep_banned(id):
        async with (await pool()).acquire() as conn:
            await conn.execute(
                "insert into reportban (uid, time) values ($1, $2)", id, None
            )
    await messagereply(message, await messages.repban())


@bl.chat_message(SearchCMD("repunban"))
async def repunban(message: Message):
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await messagereply(message, await messages.repunban_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "delete from reportban where uid=$1 returning 1", id
        ):
            return await messagereply(message, await messages.repunban_noban())
    await messagereply(message, await messages.repunban())


@bl.chat_message(SearchCMD("repbanlist"))
async def repbanlist(message: Message):
    async with (await pool()).acquire() as conn:
        repban = await conn.fetch("select uid from reportban")
    msg = f"⚛ Список пользователей в reportban бота (Всего : {len(repban)})\n\n"
    for user in repban:
        msg += f"➖ {user[0]} : | [id{user[0]}|{await get_user_name(user[0])}]\n"
    await messagereply(message, msg)


@bl.chat_message(SearchCMD("chatsstats"))
async def chatsstats(message: Message):
    async with (await pool()).acquire() as conn:
        nm = await conn.fetchval(
            "select count(*) as c from settings where setting='nightmode' and pos=true"
        )
        c = await conn.fetchval(
            "select count(*) as c from settings where setting='captcha' and pos=true"
        )
    msg = (
        f"🌓 Ночной режим включен в: {point_words(nm or 0, ['беседе', 'беседах', 'беседах'])}\n"
        f"🔢 Капча включена в: {point_words(c or 0, ['беседе', 'беседах', 'беседах'])}"
    )
    await messagereply(message, msg)


@bl.chat_message(SearchCMD("linked"))
async def linked(message: Message):
    async with (await pool()).acquire() as conn:
        c = await conn.fetchval(
            "select count(*) as c from tglink where tgid IS NOT NULL"
        )
    await messagereply(
        message,
        f"Связано с Telegram : {point_words(c, ('аккаунт', 'аккаунта', 'аккаунтов'))}.",
    )


@bl.chat_message(SearchCMD("promocreate"))
async def promocreate(message: Message):
    data = message.text.split()
    if (
        len(data) not in (5, 6)
        or not data[2].isdigit()
        or data[3] not in ("xp", "coins")
    ):
        return await messagereply(message, await messages.promocreate_hint())
    usage, date, amnt, promo_type = None, None, int(data[2]), data[3]
    try:
        if data[4].isdigit():
            usage = int(data[4])
            date = datetime.strptime(data[5], "%d.%m.%Y") if len(data) > 5 else None
        else:
            date = datetime.strptime(data[4], "%d.%m.%Y")
    except ValueError:
        return await messagereply(message, await messages.promocreate_hint())
    async with (await pool()).acquire() as conn:
        if await conn.fetchval(
            "select exists(select 1 from promocodes where code=$1)", data[1]
        ):
            return await messagereply(
                message, await messages.promocreate_alreadyexists(data[1])
            )
        await conn.execute(
            "insert into promocodes (code, usage, date, amnt, type) values ($1, $2, $3, $4, $5)",
            data[1],
            usage,
            (date.timestamp() + 86399) if date else None,
            amnt,
            promo_type,
        )
    await messagereply(
        message, await messages.promocreate(data[1], amnt, usage, date, promo_type)
    )


@bl.chat_message(SearchCMD("promodel"))
async def promodel(message: Message):
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(message, await messages.promodel_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "delete from promocodes where code=$1 returning 1", data[1]
        ):
            return await messagereply(
                message, await messages.promodel_notfound(data[1])
            )
    await messagereply(message, await messages.promodel(data[1]))


@bl.chat_message(SearchCMD("promolist"))
async def promolist(message: Message):
    async with (await pool()).acquire() as conn:
        promos = await conn.fetch(
            "select code from promocodeuses where code=ANY($1)",
            [i[0] for i in await conn.fetch("select code from promocodes")],
        )  # ????????????????????????????????
    promos = [i[0] for i in promos]
    await messagereply(
        message, await messages.promolist({k: promos.count(k) for k in set(promos)})
    )


@bl.chat_message(SearchCMD("allowinvite"))
async def allowinvite(message: Message):
    data = message.text.split()
    if len(data) != 2 or data[1] not in ("1", "2"):
        return await messagereply(message, await messages.allowinvite_hint())
    if data[-1] == "1":
        async with (await pool()).acquire() as conn:
            await conn.execute(
                "insert into referralbonus (chat_id) values ($1) on conflict (chat_id) do nothing",
                message.chat_id,
            )
        await messagereply(message, await messages.allowinvite_on())
    else:
        async with (await pool()).acquire() as conn:
            await conn.execute(
                "delete from referralbonus where chat_id=$1", message.chat_id
            )
        await messagereply(message, await messages.allowinvite_off())


@bl.chat_message(SearchCMD("prempromocreate"))
async def prempromocreate(message: Message):
    data = message.text.split()
    if len(data) != 4 or not data[2].isdigit():
        return await messagereply(message, await messages.prempromocreate_hint())
    try:
        date = datetime.strptime(data[3], "%d.%m.%Y")
    except ValueError:
        return await messagereply(message, await messages.prempromocreate_hint())
    async with (await pool()).acquire() as conn:
        if await conn.fetchval(
            "select exists(select 1 from prempromo where promo=$1)", data[1]
        ):
            return await messagereply(
                message, await messages.prempromocreate_alreadyexists(data[1])
            )
        await conn.execute(
            'insert into prempromo (promo, val, start, "end", uid) values ($1, $2, $3, $4, null)',
            data[1],
            int(data[2]),
            time.time(),
            (date.timestamp() + 86399),
        )
    await messagereply(message, await messages.prempromocreate(data[1], data[2], date))


@bl.chat_message(SearchCMD("prempromodel"))
async def prempromodel(message: Message):
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(message, await messages.prempromodel_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "delete from prempromo where promo=$1 returning 1", data[1]
        ):
            return await messagereply(
                message, await messages.prempromodel_notfound(data[1])
            )
    await messagereply(message, await messages.prempromodel(data[1]))


@bl.chat_message(SearchCMD("prempromolist"))
async def prempromolist(message: Message):
    async with (await pool()).acquire() as conn:
        promos = await conn.fetch('select promo, "end" from prempromo')
    await messagereply(message, await messages.prempromolist(promos))


@bl.chat_message(SearchCMD("bonuslist"))
async def bonuslist(message: Message):
    async with (await pool()).acquire() as conn:
        users = await conn.fetch(
            "select uid, streak from bonus order by streak desc limit 50"
        )
    await messagereply(
        message,
        "\n".join(
            [
                f"{k + 1}. [id{i[0]}|{await get_user_name(i[0])}] - Серия: {point_words(i[1] + 1, ('день', 'дня', 'дней'))}"
                for k, i in enumerate(users)
            ]
        ),
    )


@bl.chat_message(SearchCMD("rewardscount"))
async def rewardscount(message: Message):
    async with (await pool()).acquire() as conn:
        users = await conn.fetch("select deactivated from rewardscollected")
    await messagereply(
        message,
        f"Число пользователей, активировавших /rewards: {len(users)}. Из них отписалось: {len([i for i in users if i[0]])}",
    )
