import time
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from StarManager.core import managers
from StarManager.core.config import api
from StarManager.core.db import pool
from StarManager.core.utils import (
    delete_messages,
    get_chat_name,
    get_group_name,
    get_pool,
    get_user_ban,
    get_user_name,
    get_user_nickname,
    is_higher,
    kick_user,
    messagereply,
    search_id_in_message,
    send_message,
)
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.checkers import haveAccess
from StarManager.vkbot.rules import SearchCMD

bl = BotLabeler()


@bl.chat_message(SearchCMD("skick"))
async def skick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if not id or len(data) < 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.skick_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if uid == id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.kick_myself()
        )

    try:
        kick_cause = " ".join(data[3:])
        if kick_cause == str(id) or len(kick_cause) == 0:
            kick_cause = "Причина не указана"
    except Exception:
        kick_cause = "Причина не указана"

    if not (chats := await get_pool(chat_id, data[1])):
        return await messagereply(
            message, disable_mentions=1, message=await messages.s_invalid_group(data[1])
        )

    u_nickname = await get_user_nickname(uid, chat_id)
    ch_nickname = await get_user_nickname(id, chat_id)
    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.skick_start(
            uid, u_name, u_nickname, id, ch_name, ch_nickname, len(chats), data[1]
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "skick", chat_id, uid
        ):
            continue
        ch_nickname = await get_user_nickname(id, chat_id)
        u_nickname = await get_user_nickname(uid, chat_id)
        if await kick_user(id, chat_id):
            await send_message(
                peer_ids=chat_id + 2000000000,
                msg=await messages.kick(
                    u_name, u_nickname, uid, ch_name, ch_nickname, id, kick_cause
                ),
            )
            success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.skick(
            id,
            ch_name,
            await get_user_nickname(id, edit.peer_id - 2000000000),
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("sban"))
async def sban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if not id or len(data) < 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.sban_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if uid == id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.ban_myself()
        )

    if not (chats := await get_pool(chat_id, data[1])):
        return await messagereply(
            message, disable_mentions=1, message=await messages.s_invalid_group(data[1])
        )

    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    u_nickname = await get_user_nickname(uid, chat_id)
    ch_nickname = await get_user_nickname(id, chat_id)

    if message.reply_message is None:
        cdata = data[3:]
    else:
        cdata = data[2:]

    if len(cdata) >= 1:
        if cdata[0].isdigit():
            ban_time = abs(int(cdata[0])) * 86400
            ban_cause = " ".join(cdata[1:]) if len(cdata) > 1 else None
        else:
            ban_time = 86400 * 365
            ban_cause = " ".join(cdata[0:])
    else:
        ban_time = 86400 * 365
        ban_cause = None

    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.sban_start(
            uid, u_name, u_nickname, id, ch_name, ch_nickname, len(chats), data[1]
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "sban", chat_id, uid
        ):
            continue
        if await get_user_ban(id, chat_id) >= time.time():
            continue
        msg = await messages.ban(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            await get_user_nickname(id, chat_id),
            ban_cause,
            ban_time // 86400,
        )
        await managers.ban.ban(
            id,
            chat_id,
            ban_time,
            ban_cause or "Без указания причины",
            f"[id{uid}|{u_name}]",
        )

        if await kick_user(id, chat_id):
            await send_message(msg=msg, peer_ids=chat_id + 2000000000)
        success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.sban(
            id,
            ch_name,
            await get_user_nickname(id, edit.peer_id - 2000000000),
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("sunban"))
async def sunban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if not id or len(data) < 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.sunban_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if uid == id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unban_myself()
        )

    if not (chats := await get_pool(chat_id, data[1])):
        return await messagereply(
            message, disable_mentions=1, message=await messages.s_invalid_group(data[1])
        )

    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.sunban_start(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            id,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
            len(chats),
            data[1],
        ),
    )
    success = 0
    for chat_id in chats:
        if (
            not await is_higher(uid, id, chat_id)
            or not await haveAccess("sunban", chat_id, uid)
            or await get_user_ban(id, chat_id) <= time.time()
        ):
            continue
        if await managers.ban.unban(id, chat_id):
            success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.sunban(
            id,
            await get_user_name(id),
            await get_user_nickname(id, edit.peer_id - 2000000000),
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("ssnick"))
async def ssnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if not id or (
        (len(data) < 4 and message.reply_message is None)
        or (len(data) < 3 and message.reply_message is not None)
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.ssnick_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if not (chats := await get_pool(chat_id, data[1])):
        return await messagereply(
            message, disable_mentions=1, message=await messages.s_invalid_group(data[1])
        )

    nickname = (
        " ".join(data[3:]) if message.reply_message is None else " ".join(data[2:])
    )
    if not (46 >= len(nickname) and ("[" not in nickname and "]" not in nickname)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.ssnick_hint()
        )

    u_name = await get_user_name(uid)
    name = await get_user_name(id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.ssnick_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            name,
            await get_user_nickname(id, chat_id),
            len(chats),
            data[1],
        ),
    )
    success = 0
    for chat_id in chats:
        if uid != id:
            if not await is_higher(uid, id, chat_id):
                continue
        if not await haveAccess("ssnick", chat_id, uid):
            continue

        async with (await pool()).acquire() as conn:
            ch_nick = await conn.fetchval(
                "select nickname from nickname where chat_id=$1 and uid=$2", chat_id, id
            )
            u_nick = await conn.fetchval(
                "select nickname from nickname where chat_id=$1 and uid=$2",
                chat_id,
                uid,
            )
            if not await conn.fetchval(
                "update nickname set nickname = $1 where chat_id=$2 and uid=$3 returning 1",
                nickname,
                chat_id,
                id,
            ):
                await conn.execute(
                    "insert into nickname (uid, chat_id, nickname) values ($1, $2, $3)",
                    id,
                    chat_id,
                    nickname,
                )
        await send_message(
            chat_id + 2000000000,
            await messages.snick(uid, u_name, u_nick, id, name, ch_nick, nickname),
        )
        success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.ssnick(
            id,
            name,
            await get_user_nickname(id, edit.peer_id - 2000000000),
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("srnick"))
async def srnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if not id or len(data) < 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.srnick_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if not (chats := await get_pool(chat_id, data[1])):
        return await messagereply(
            message, disable_mentions=1, message=await messages.s_invalid_group(data[1])
        )

    ch_name = await get_user_name(id)
    u_name = await get_user_name(uid)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.srnick_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            await get_user_nickname(id, chat_id),
            len(chats),
            data[1],
        ),
    )
    success = 0
    for chat_id in chats:
        if uid != id:
            if not await is_higher(uid, id, chat_id):
                continue
        if not await haveAccess("srnick", chat_id, uid):
            continue
        async with (await pool()).acquire() as conn:
            if await conn.fetchval(
                "delete from nickname where chat_id=$1 and uid=$2 returning 1",
                chat_id,
                id,
            ):
                await send_message(
                    chat_id + 200000000,
                    await messages.rnick(
                        uid,
                        u_name,
                        await get_user_nickname(uid, chat_id),
                        id,
                        ch_name,
                        await get_user_nickname(id, chat_id),
                    ),
                )
                success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.srnick(id, ch_name, len(chats), success),
    )


@bl.chat_message(SearchCMD("szov"))
async def szov(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) < 3:
        return await messagereply(
            message, disable_mentions=1, message=await messages.szov_hint()
        )

    if not (chats := await get_pool(chat_id, data[1])):
        return await messagereply(
            message, disable_mentions=1, message=await messages.s_invalid_group(data[1])
        )

    name = await get_user_name(uid)
    nickname = await get_user_nickname(uid, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.szov_start(uid, name, nickname, len(chats), data[1]),
    )
    success = 0
    text = " ".join(data[2:])
    for chat_id in chats:
        if not await haveAccess("szov", chat_id, uid):
            continue
        try:
            members = await api.messages.get_conversation_members(
                peer_id=chat_id + 2000000000,
                fields=["deactivated"],  # type: ignore
            )
            if not await send_message(
                peer_ids=chat_id + 2000000000,
                msg=await messages.zov(
                    uid,
                    name,
                    await get_user_nickname(uid, chat_id),
                    text,
                    members.items,
                ),
                disable_mentions=False,
            ):
                raise Exception
            success += 1
        except Exception:
            pass

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.szov(
            uid,
            name,
            await get_user_nickname(uid, edit.peer_id - 2000000000),
            data[1],
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("chat"))
async def chat(message: Message):
    chat_id = message.peer_id - 2000000000
    members = (
        await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    ).items
    id = [i for i in members if i.is_admin and i.is_owner][0].member_id

    names = await api.users.get(user_ids=[id])
    try:
        name = f"{names[0].first_name} {names[0].last_name}"
        prefix = "id"
    except Exception:
        prefix = "club"
        name = await get_group_name(-int(id))

    async with (await pool()).acquire() as conn:
        chatgroup = (
            "Привязана"
            if await conn.fetchval(
                "select exists(select 1 from chatgroups where chat_id=$1)", chat_id
            )
            else "Не привязана"
        )
        gpool = (
            "Привязана"
            if await conn.fetchval(
                "select exists(select 1 from gpool where chat_id=$1)", chat_id
            )
            else "Не привязана"
        )

        now = time.time()
        muted = len([i for i in await managers.mute.get_all(chat_id) if i.mute > now])
        banned = len(await managers.ban.get_all(chat_id))

        if bjd := await conn.fetchval(
            "select time from botjoineddate where chat_id=$1", chat_id
        ):
            bjd = datetime.utcfromtimestamp(bjd).strftime("%d.%m.%Y %H:%M")
        else:
            bjd = "Невозможно определить"

    if (chat := await managers.public_chats.get_chat(chat_id)) and chat.isopen:
        public = "Открытый"
    else:
        public = "Приватный"

    if chat and chat.premium:
        prem = "Есть"
    else:
        prem = "Отсутствует"

    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.chat(
            abs(id),
            name,
            chat_id,
            chatgroup,
            gpool,
            public,
            muted,
            banned,
            len(members),
            bjd,
            prefix,
            await get_chat_name(chat_id),
            prem,
        ),
        keyboard=None
        if not await haveAccess("settings", chat_id, message.from_id)
        else (keyboard.chat(message.from_id, public == "Открытый")),
    )


@bl.chat_message(SearchCMD("antitag"))
async def antitag(message: Message):
    data = message.text.split()
    if (
        len(data) != 3
        or data[1] not in ("add", "del")
        or not (
            id := await search_id_in_message(message.text, message.reply_message, 3)
        )
    ):
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.antitag(),
            keyboard=keyboard.antitag(message.from_id),
        )
    chat_id = message.peer_id - 2000000000
    if data[1] == "add":
        await managers.antitag.add(id, chat_id)
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.antitag_add(
                id, await get_user_name(id), await get_user_nickname(id, chat_id)
            ),
        )
    await managers.antitag.remove(id, chat_id)
    return await messagereply(
        message,
        disable_mentions=1,
        message=await messages.antitag_del(
            id, await get_user_name(id), await get_user_nickname(id, chat_id)
        ),
    )


@bl.chat_message(SearchCMD("pin"))
async def pin(message: Message):
    if not message.reply_message:
        return await messagereply(
            message, disable_mentions=1, message=await messages.pin_hint()
        )
    try:
        if not await api.messages.pin(
            message.peer_id, message.reply_message.conversation_message_id
        ):
            raise Exception
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.pin_cannot()
        )
    else:
        await delete_messages(message.conversation_message_id, message.chat_id)


@bl.chat_message(SearchCMD("unpin"))
async def unpin(message: Message):
    chat_settings = (
        (await api.messages.get_conversations_by_id(peer_ids=[message.peer_id]))
        .items[0]
        .chat_settings
    )
    if not chat_settings or not chat_settings.pinned_message:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unpin_notpinned()
        )
    try:
        if not await api.messages.unpin(message.peer_id):
            raise Exception
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unpin_cannot()
        )
    else:
        await delete_messages(message.conversation_message_id, message.chat_id)
