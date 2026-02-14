import asyncio
import re
import time
from datetime import datetime, timedelta

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from StarManager.core import managers
from StarManager.core.config import api
from StarManager.core.utils import (
    get_silence,
    get_user_access_level,
    get_user_ban,
    get_user_name,
    get_user_nickname,
    kick_user,
    messagereply,
    search_id_in_message,
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
    await managers.logs.add_log(message.from_id, message.chat_id, 1, "/timeout")


@bl.chat_message(SearchCMD("inactive"))
async def inactive(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) != 3:
        return await messagereply(
            message, disable_mentions=1, message=await messages.inactive_hint()
        )

    mode, value, m = data[1].lower(), data[2], None
    try:
        cutoff = datetime.strptime(value, "%d.%m.%Y").timestamp()
        m = 1
    except ValueError:
        m = re.match(r"^(\d+)([dwm])$", (value if not value.isdigit() else value + "d"))
        if m:
            num, unit = int(m.group(1)), m.group(2)
            now = datetime.now()
            if unit == "d":
                cutoff = now - timedelta(days=num)
            elif unit == "w":
                cutoff = now - timedelta(weeks=num)
            else:
                cutoff = now - timedelta(days=30 * num)
            cutoff = cutoff.timestamp()

    if mode not in ("chat", "vk") or not m:
        return await messagereply(
            message, disable_mentions=1, message=await messages.inactive_hint()
        )

    to_kick = []
    chat_members = await api.messages.get_conversation_members(
        message.peer_id,
        fields=["last_seen"],  # type: ignore
    )

    if mode == "chat":
        res = await managers.lastmessagedate.get_all(chat_id)
        for row in res:
            if row.last_message < cutoff:
                to_kick.append(row.uid)
    else:
        if not chat_members or not chat_members.profiles:
            return await messagereply(
                message, disable_mentions=1, message=await messages.notadmin()
            )
        for member in chat_members.profiles:
            if (
                member.last_seen
                and member.last_seen.time
                and member.last_seen.time < cutoff
            ):
                to_kick.append(member.id)

    u_name = await get_user_name(uid)
    kicked = 0
    for user in to_kick:
        kicked += await kick_user(user, chat_id)
        await asyncio.sleep(0.35)
        await managers.logs.add_log(
            user, chat_id, 2, "Кик из чата", by_name=f"[id{message.from_id}|{u_name}]"
        )

    if not kicked:
        return await messagereply(
            message, disable_mentions=1, message=await messages.inactive_no_results()
        )

    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.inactive(
            uid, u_name, await get_user_nickname(uid, chat_id), kicked
        ),
    )
    await managers.logs.add_log(
        message.from_id, message.chat_id, 1, f"/inactive {' '.join(data[1:])}"
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

    u_name = await get_user_name(uid)
    await managers.ban.ban(
        id,
        chat_id,
        ban_time,
        ban_cause or "Без указания причины",
        f"[id{uid}|{u_name}]",
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
    await managers.logs.add_log(
        message.from_id, message.chat_id, 1, f"/ban {' '.join(data[1:])}"
    )
    await managers.logs.add_log(
        id,
        message.chat_id,
        2,
        f"Выдача блокировки на {ban_time // 86400} дней",
        by_name=f"[id{message.from_id}|{u_name}]",
        reason=ban_cause,
    )


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

    await managers.ban.unban(id, chat_id)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.unban(
            u_name := await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            uid,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
            id,
        ),
        keyboard=keyboard.deletemessages(uid, [message.conversation_message_id]),
    )
    await managers.logs.add_log(
        message.from_id, message.chat_id, 1, f"/unban {' '.join(data[1:])}"
    )
    await managers.logs.add_log(
        id,
        message.chat_id,
        2,
        "Снятие блокировки",
        by_name=f"[id{message.from_id}|{u_name}]",
    )


@bl.chat_message(SearchCMD("banlist"))
async def banlist(message: Message):
    now = time.time()
    res = [
        i
        for i in await managers.ban.get_all(message.peer_id - 2000000000)
        if i and i.ban > now
    ]
    count = len(res)
    res = sorted(
        res[:30],
        key=lambda i: i.uid,
        reverse=True,
    )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.banlist(res, count),
        keyboard=keyboard.banlist(message.from_id, 0, count),
    )
    await managers.logs.add_log(message.from_id, message.chat_id, 1, "/banlist")


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
                await api.messages.get_conversation_members(
                    peer_id=message.peer_id,
                    fields=["deactivated"],  # type: ignore
                )
            ).items,
        ),
        disable_mentions=0,
    )
    await managers.logs.add_log(message.from_id, message.chat_id, 1, f"/zov {' '.join(data[1:])}")


@bl.chat_message(SearchCMD("kickmenu"))
async def kickmenu(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.kickmenu(),
        keyboard=keyboard.kickmenu(message.from_id),
    )
    await managers.logs.add_log(message.from_id, message.chat_id, 1, "/kickmenu")
