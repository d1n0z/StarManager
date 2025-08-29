import time
from ast import literal_eval
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from StarManager.core.config import api
from StarManager.core.db import pool
from StarManager.core.utils import (
    search_id_in_message,
    get_silence,
    get_user_access_level,
    get_user_ban,
    get_user_name,
    get_user_nickname,
    kick_user,
    messagereply,
)
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.rules import SearchCMD

bl = BotLabeler()


@bl.chat_message(SearchCMD("timeout"))
async def timeout(message: Message):
    activated = await get_silence(message.peer_id - 2000000000)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.timeout(activated),
        keyboard=keyboard.timeout(message.from_id, activated),
    )


@bl.chat_message(SearchCMD("inactive"))
async def inactive(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.inactive_hint()
        )
    count = data[1]
    if not count.isdigit() or (count := int(count)) <= 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.inactive_hint()
        )
    count = time.time() - count * 86400
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            "select uid from lastmessagedate where chat_id=$1 and uid>0 and last_message<$2",
            chat_id,
            count,
        )
    kicked = 0
    if len(res) <= 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.inactive_no_results()
        )
    members = await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = [i.member_id for i in members.items if i.member_id > 0]
    for i in res:
        if i[0] in members:
            try:
                x = await kick_user(i[0], chat_id)
                kicked += x
            except Exception:
                pass
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.inactive(
            uid, await get_user_name(uid), await get_user_nickname(uid, chat_id), kicked
        ),
    )


@bl.chat_message(SearchCMD("ban"))
async def ban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if id == uid:
        return await messagereply(
            message, disable_mentions=1, message=await messages.ban_myself()
        )
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.ban_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if message.reply_message is None:
        if len(data) == 2:
            ban_time = 3650 * 86400
            ban_cause = None
        else:
            if data[2].isdigit():
                ban_time = int(data[2]) * 86400
                if ban_time > 86400 * 3650:
                    msg = await messages.ban_maxtime()
                    await messagereply(message, disable_mentions=1, message=msg)
                    return
                ban_cause = None if len(data) == 3 else " ".join(data[3:])
            else:
                ban_time = 3650 * 86400
                ban_cause = " ".join(data[2:])
    else:
        if len(data) == 1:
            ban_time = 3650 * 86400
            ban_cause = None
        else:
            if data[1].isdigit():
                ban_time = int(data[1]) * 86400
                if ban_time > 86400 * 3650:
                    msg = await messages.ban_maxtime()
                    await messagereply(message, disable_mentions=1, message=msg)
                    return
                ban_cause = None if len(data) == 2 else " ".join(data[2:])
            else:
                ban_time = 3650 * 86400
                ban_cause = " ".join(data[1:])
    if ban_time <= 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.ban_hint()
        )

    if await get_user_access_level(id, chat_id) >= await get_user_access_level(
        uid, chat_id
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.ban_higher()
        )

    if (ch_ban := await get_user_ban(id, chat_id)) >= time.time():
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.already_banned(
                await get_user_name(id),
                await get_user_nickname(id, chat_id),
                id,
                ch_ban,
            ),
        )

    ban_date = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    async with (await pool()).acquire() as conn:
        res = await conn.fetchrow(
            "select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates from ban where "
            "chat_id=$1 and uid=$2",
            chat_id,
            id,
        )
    if res is not None:
        ban_times = literal_eval(res[0])
        ban_causes = literal_eval(res[1])
        ban_names = literal_eval(res[2])
        ban_dates = literal_eval(res[3])
    else:
        ban_times, ban_causes, ban_names, ban_dates = [], [], [], []

    if ban_cause is None:
        ban_cause = "Без указания причины"
    if ban_date is None:
        ban_date = "Дата неизвестна"
    ban_times.append(ban_time)
    ban_causes.append(ban_cause)
    u_name = await get_user_name(uid)
    ban_names.append(f"[id{uid}|{u_name}]")
    ban_dates.append(ban_date)

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update ban set ban = $1, last_bans_times = $2, last_bans_causes = $3, last_bans_names = $4, "
            "last_bans_dates = $5 where chat_id=$6 and uid=$7 returning 1",
            time.time() + ban_time,
            f"{ban_times}",
            f"{ban_causes}",
            f"{ban_names}",
            f"{ban_dates}",
            chat_id,
            id,
        ):
            await conn.execute(
                "insert into ban (uid, chat_id, ban, last_bans_times, last_bans_causes, last_bans_names, "
                "last_bans_dates) values ($1, $2, $3, $4, $5, $6, $7)",
                id,
                chat_id,
                time.time() + ban_time,
                f"{ban_times}",
                f"{ban_causes}",
                f"{ban_names}",
                f"{ban_dates}",
            )

    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.ban(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
            ban_cause,
            ban_time // 86400,
        )
        + (
            "\n❗ Пользователя не удалось кикнуть"
            if not await kick_user(id, chat_id)
            else ""
        ),
        keyboard=keyboard.punish_unpunish(
            uid, id, "ban", message.conversation_message_id
        ),
    )
    return


@bl.chat_message(SearchCMD("unban"))
async def unban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if id == uid:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unban_myself()
        )
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unban_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if await get_user_access_level(id, chat_id) >= await get_user_access_level(
        uid, chat_id
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.unban_higher()
        )
    if await get_user_ban(id, chat_id) <= time.time():
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.unban_no_ban(
                id, await get_user_name(id), await get_user_nickname(id, chat_id)
            ),
        )
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "update ban set ban = 0 where chat_id=$1 and uid=$2", chat_id, id
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.unban(
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            uid,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
            id,
        ),
        keyboard=keyboard.deletemessages(uid, [message.conversation_message_id]),
    )


@bl.chat_message(SearchCMD("banlist"))
async def banlist(message: Message):
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            "select uid, chat_id, last_bans_causes, ban, last_bans_names from ban where chat_id=$1 and "
            "ban>$2 order by uid desc",
            message.peer_id - 2000000000,
            time.time(),
        )
    count = len(res)
    res = res[:30]
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.banlist(res, count),
        keyboard=keyboard.banlist(message.from_id, 0, count),
    )


@bl.chat_message(SearchCMD("zov"))
async def zov(message: Message):
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=await messages.zov_hint()
        )
    await messagereply(
        message,
        message=await messages.zov(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, message.peer_id - 2000000000),
            " ".join(data[1:]),
            (
                await api.messages.get_conversation_members(peer_id=message.peer_id)
            ).items,
        ),
    )


@bl.chat_message(SearchCMD("kickmenu"))
async def kickmenu(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.kickmenu(),
        keyboard=keyboard.kickmenu(message.from_id),
    )
