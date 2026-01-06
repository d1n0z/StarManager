import time

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from StarManager.core import managers
from StarManager.core.config import api
from StarManager.core.db import pool
from StarManager.core.utils import (
    edit_message,
    get_gpool,
    get_user_ban,
    get_user_name,
    get_user_nickname,
    get_user_warns,
    is_higher,
    kick_user,
    messagereply,
    search_id_in_message,
    send_message,
    set_chat_mute,
)
from StarManager.vkbot import messages
from StarManager.vkbot.checkers import haveAccess
from StarManager.vkbot.rules import SearchCMD

bl = BotLabeler()


@bl.chat_message(SearchCMD("gkick"))
async def gkick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if id == uid:
        return await messagereply(
            message, disable_mentions=1, message=await messages.kick_myself()
        )
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gkick_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    data = message.text.split()
    if message.reply_message is None:
        kick_cause = " ".join(data[2:])
    else:
        kick_cause = " ".join(data[1:])
    if len(kick_cause) == 0:
        kick_cause = "Причина не указана"

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    ch_name = await get_user_name(id)
    u_name = await get_user_name(uid)
    ch_nickname = await get_user_nickname(id, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gkick_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            ch_nickname,
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gkick", chat_id, uid
        ):
            continue
        if await kick_user(id, chat_id):
            try:
                await send_message(
                    peer_ids=chat_id + 2000000000,
                    msg=await messages.kick(
                        u_name,
                        await get_user_nickname(uid, chat_id),
                        uid,
                        ch_name,
                        await get_user_nickname(id, chat_id),
                        id,
                        kick_cause,
                    ),
                )
            except Exception:
                pass
            success += 1

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gkick(id, ch_name, ch_nickname, len(chats), success),
    )


@bl.chat_message(SearchCMD("gban"))
async def gban(message: Message):
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
            message, disable_mentions=1, message=await messages.gban_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if message.reply_message is None:
        if len(data) == 2:
            ban_time = 365 * 86400
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
                ban_time = 365 * 86400
                ban_cause = " ".join(data[2:])
    else:
        if len(data) == 1:
            ban_time = 365 * 86400
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
                ban_time = 365 * 86400
                ban_cause = " ".join(data[1:])
    if ban_time <= 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gban_hint()
        )

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    ch_nick = await get_user_nickname(id, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gban_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            ch_nick,
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gban", chat_id, uid
        ):
            continue

        await managers.ban.ban(
            id,
            chat_id,
            ban_time,
            ban_cause or "Без указания причины",
            f"[id{uid}|{u_name}]",
        )
        if await kick_user(id, chat_id):
            await send_message(
                msg=await messages.ban(
                    uid,
                    u_name,
                    await get_user_nickname(uid, chat_id),
                    id,
                    ch_name,
                    await get_user_nickname(id, chat_id),
                    ban_cause,
                    ban_time // 86400,
                ),
                peer_ids=chat_id + 2000000000,
            )
        success += 1

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gban(id, ch_name, ch_nick, len(chats), success),
    )


@bl.chat_message(SearchCMD("gunban"))
async def gunban(message: Message):
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
            message, disable_mentions=1, message=await messages.gunban_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    name = await get_user_name(id)
    nick = await get_user_nickname(id, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gunban_start(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            id,
            name,
            nick,
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gunban", chat_id, uid
        ):
            continue
        if await get_user_ban(id, chat_id) <= time.time():
            continue
        if await managers.ban.unban(id, chat_id):
            success += 1

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gunban(id, name, nick, len(chats), success),
    )


@bl.chat_message(SearchCMD("gmute"))
async def gmute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if id == uid:
        return await messagereply(
            message, disable_mentions=1, message=await messages.mute_myself()
        )
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gmute_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    try:
        if message.reply_message is None:
            mute_time = int(data[2]) * 60
        else:
            mute_time = int(data[1]) * 60
        if mute_time <= 0:
            raise
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gmute_hint()
        )

    if message.reply_message is None:
        mute_cause = " ".join(data[3:])
    else:
        mute_cause = " ".join(data[2:])

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    ch_nick = await get_user_nickname(uid, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gmute_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            ch_nick,
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gmute", chat_id, uid
        ):
            continue

        await managers.mute.mute(
            id,
            chat_id,
            mute_time,
            mute_cause or "Без указания причины",
            f"[id{uid}|{u_name}]",
        )

        await set_chat_mute(id, chat_id, mute_time)
        await send_message(
            peer_ids=chat_id + 2000000000,
            msg=await messages.mute(
                u_name,
                await get_user_nickname(uid, chat_id),
                uid,
                ch_name,
                await get_user_nickname(id, chat_id),
                id,
                mute_cause,
                int(mute_time / 60),
            ),
        )
        success += 1

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gmute(id, ch_name, ch_nick, len(chats), success),
    )


@bl.chat_message(SearchCMD("gunmute"))
async def gunmute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if id == uid:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unmute_myself()
        )
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gunmute_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    ch_nick = await get_user_nickname(id, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gunmute_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            ch_nick,
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gunmute", chat_id, uid
        ):
            continue
        if not await managers.mute.unmute(id, chat_id):
            continue
        await set_chat_mute(id, chat_id, 0)
        await send_message(
            peer_ids=chat_id + 2000000000,
            msg=await messages.unmute(
                u_name,
                await get_user_nickname(uid, chat_id),
                uid,
                ch_name,
                await get_user_nickname(id, chat_id),
                id,
            ),
        )
        success += 1

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gunmute(id, ch_name, ch_nick, len(chats), success),
    )


@bl.chat_message(SearchCMD("gwarn"))
async def gwarn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if id == uid:
        return await messagereply(
            message, disable_mentions=1, message=await messages.warn_myself()
        )
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gwarn_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    if message.reply_message is None:
        warn_cause = " ".join(data[2:])
    else:
        warn_cause = " ".join(data[1:])
    if not warn_cause:
        warn_cause = "Без указания причины"

    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    ch_nick = await get_user_nickname(id, chat_id)
    msg = await messages.gwarn_start(
        uid,
        u_name,
        await get_user_nickname(uid, chat_id),
        id,
        ch_name,
        ch_nick,
        len(chats),
    )
    edit = await messagereply(message, disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gwarn", chat_id, uid
        ):
            continue

        warns = await managers.warn.warn(id, chat_id, warn_cause, f"[id{uid}|{u_name}]")
        if warns >= 3:
            await kick_user(id, chat_id)
            msg = await messages.warn_kick(
                u_name,
                await get_user_nickname(uid, chat_id),
                uid,
                ch_name,
                await get_user_nickname(id, chat_id),
                id,
                warn_cause,
            )
        else:
            msg = await messages.warn(
                u_name,
                await get_user_nickname(uid, chat_id),
                uid,
                ch_name,
                await get_user_nickname(id, chat_id),
                id,
                warn_cause,
            )

        await send_message(msg=msg, peer_ids=chat_id + 2000000000)
        success += 1

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gwarn(id, ch_name, ch_nick, len(chats), success),
    )


@bl.chat_message(SearchCMD("gunwarn"))
async def gunwarn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if id == uid:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unwarn_myself()
        )
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gunwarn_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    ch_nick = await get_user_nickname(id, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gunwarn_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            ch_nick,
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gunwarn", chat_id, uid
        ):
            continue
        ch_warns = await get_user_warns(id, chat_id)
        if ch_warns == 0:
            continue
        if not await managers.warn.unwarn(id, chat_id):
            continue
        await send_message(
            peer_ids=chat_id + 2000000000,
            msg=await messages.unwarn(
                u_name,
                await get_user_nickname(uid, chat_id),
                uid,
                ch_name,
                await get_user_nickname(id, chat_id),
                id,
            ),
        )
        success += 1

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gunwarn(id, ch_name, ch_nick, len(chats), success),
    )


@bl.chat_message(SearchCMD("gsnick"))
async def gsnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gsnick_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if message.reply_message is None:
        nickname = " ".join(data[2:])
    else:
        nickname = " ".join(data[1:])
    if len(nickname) > 46 or "[" in nickname or "]" in nickname:
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.snick_too_long_nickname(),
        )
    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    ch_nick = await get_user_nickname(id, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gsnick_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            ch_nick,
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await haveAccess("gsnick", chat_id, uid):
            continue
        if uid != id:
            if not await is_higher(uid, id, chat_id):
                continue

        async with (await pool()).acquire() as conn:
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
            peer_ids=chat_id + 2000000000,
            msg=await messages.snick(
                uid,
                u_name,
                await get_user_nickname(uid, chat_id),
                id,
                ch_name,
                await get_user_nickname(id, chat_id),
                nickname,
            ),
        )
        success += 1

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gsnick(id, ch_name, ch_nick, len(chats), success),
    )


@bl.chat_message(SearchCMD("grnick"))
async def grnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.grnick_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    u_name = await get_user_name(uid)
    ch_name = await get_user_name(id)
    ch_nick = await get_user_nickname(id, chat_id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.grnick_start(
            uid,
            u_name,
            await get_user_nickname(uid, chat_id),
            id,
            ch_name,
            ch_nick,
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        ch_nickname = await get_user_nickname(id, chat_id)
        if ch_nickname is None:
            continue
        if not await haveAccess("grnick", chat_id, uid):
            continue
        if uid != id:
            if not await is_higher(uid, id, chat_id):
                continue
        try:
            await send_message(
                peer_ids=chat_id + 2000000000,
                msg=await messages.rnick(
                    uid,
                    u_name,
                    await get_user_nickname(uid, chat_id),
                    id,
                    ch_name,
                    ch_nickname,
                ),
            )
            async with (await pool()).acquire() as conn:
                await conn.execute(
                    "delete from nickname where chat_id=$1 and uid=$2", chat_id, id
                )
            success += 1
        except Exception:
            pass

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.grnick(id, ch_name, ch_nick, len(chats), success),
    )


@bl.chat_message(SearchCMD("gzov"))
async def gzov(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gzov_hint()
        )

    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    u_name = await get_user_name(uid)
    u_nick = await get_user_nickname(uid, chat_id)
    msg = await messages.gzov_start(uid, u_name, u_nick, len(chats))
    edit = await messagereply(message, disable_mentions=1, message=msg)
    success = 0
    cause = " ".join(data[1:])
    for chat_id in chats:
        if not await haveAccess("gzov", chat_id, uid):
            continue
        try:
            members = (
                await api.messages.get_conversation_members(
                    peer_id=chat_id + 2000000000,
                    fields=["deactivated"],  # type: ignore
                )
            ).items
            if not await send_message(
                peer_ids=chat_id + 2000000000,
                msg=await messages.zov(
                    uid, u_name, await get_user_nickname(uid, chat_id), cause, members
                ),
                disable_mentions=True,
            ):
                raise Exception
            success += 1
        except Exception:
            pass

    if edit is None:
        return
    await edit_message(
        peer_id=edit.peer_id,
        cmid=edit.conversation_message_id,
        msg=await messages.gzov(uid, u_name, u_nick, len(chats), success),
    )
