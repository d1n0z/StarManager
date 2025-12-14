import time
from ast import literal_eval
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from StarManager.vkbot import messages
from StarManager.vkbot.checkers import haveAccess
from StarManager.vkbot.rules import SearchCMD
from StarManager.core.utils import (
    search_id_in_message,
    get_user_access_level,
    get_user_name,
    get_user_nickname,
    kick_user,
    get_user_ban,
    set_chat_mute,
    get_user_warns,
    get_gpool,
    edit_message,
    send_message,
    messagereply,
)
from StarManager.core.config import api
from StarManager.core.db import pool

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
        u_acc = await get_user_access_level(uid, chat_id)
        if u_acc <= await get_user_access_level(id, chat_id) or not await haveAccess(
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
        u_acc = await get_user_access_level(uid, chat_id)
        if u_acc <= await get_user_access_level(id, chat_id) or not await haveAccess(
            "gban", chat_id, uid
        ):
            continue

        ban_date = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates "
                "from ban where chat_id=$1 and uid=$2",
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
        u_acc = await get_user_access_level(uid, chat_id)
        if u_acc <= await get_user_access_level(id, chat_id) or not await haveAccess(
            "gunban", chat_id, uid
        ):
            continue
        if await get_user_ban(id, chat_id) <= time.time():
            continue
        async with (await pool()).acquire() as conn:
            if await conn.fetchval(
                "update ban set ban = 0 where chat_id=$1 and uid=$2 and ban>$3 returning 1",
                chat_id,
                id,
                time.time(),
            ):
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
        u_acc = await get_user_access_level(uid, chat_id)
        if u_acc <= await get_user_access_level(id, chat_id) or not await haveAccess(
            "gmute", chat_id, uid
        ):
            continue

        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_mutes_times, last_mutes_causes, last_mutes_names, "
                "last_mutes_dates from mute where chat_id=$1 and uid=$2",
                chat_id,
                id,
            )
        if res is not None:
            mute_times = literal_eval(res[0])
            mute_causes = literal_eval(res[1])
            mute_names = literal_eval(res[2])
            mute_dates = literal_eval(res[3])
        else:
            mute_times, mute_causes, mute_names, mute_dates = [], [], [], []

        mute_date = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        if mute_cause is None:
            mute_cause = "Без указания причины"
        if mute_date is None:
            mute_date = "Дата неизвестна"

        mute_times.append(mute_time)
        mute_causes.append(mute_cause)
        mute_names.append(f"[id{uid}|{u_name}]")
        mute_dates.append(mute_date)

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update mute set mute = $1, last_mutes_times = $2, last_mutes_causes = $3, "
                "last_mutes_names = $4, last_mutes_dates = $5 where chat_id=$6 and uid=$7 returning 1",
                time.time() + mute_time,
                f"{mute_times}",
                f"{mute_causes}",
                f"{mute_names}",
                f"{mute_dates}",
                chat_id,
                id,
            ):
                await conn.execute(
                    "insert into mute (uid, chat_id, mute, last_mutes_times, last_mutes_causes, last_mutes_names, "
                    "last_mutes_dates) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                    id,
                    chat_id,
                    time.time() + mute_time,
                    f"{mute_times}",
                    f"{mute_causes}",
                    f"{mute_names}",
                    f"{mute_dates}",
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
        u_acc = await get_user_access_level(uid, chat_id)
        ch_acc = await get_user_access_level(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess("gunmute", chat_id, uid):
            continue
        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update mute set mute = 0 where chat_id=$1 and uid=$2 returning 1",
                chat_id,
                id,
            ):
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
        u_acc = await get_user_access_level(uid, chat_id)
        if u_acc <= await get_user_access_level(id, chat_id) or not await haveAccess(
            "gwarn", chat_id, uid
        ):
            continue

        warn_date = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select warns, last_warns_times, last_warns_causes, last_warns_names, last_warns_dates from warn "
                "where chat_id=$1 and uid=$2",
                chat_id,
                id,
            )
        if res is not None:
            warns = res[0] + 1
            warn_times = literal_eval(res[1])
            warn_causes = literal_eval(res[2])
            warn_names = literal_eval(res[3])
            warn_dates = literal_eval(res[4])
        else:
            warns = 1
            warn_times, warn_causes, warn_names, warn_dates = [], [], [], []
        if warn_cause is None:
            warn_cause = "Без указания причины"
        if warn_date is None:
            warn_date = "Дата неизвестна"
        warn_times.append(0)
        warn_causes.append(warn_cause)
        warn_names.append(f"[id{uid}|{u_name}]")
        warn_dates.append(warn_date)

        if warns >= 3:
            warns = 0
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

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update warn set warns = $1, last_warns_times = $2, last_warns_causes = $3, "
                "last_warns_names = $4, last_warns_dates = $5 where chat_id=$6 and uid=$7 returning 1",
                warns,
                f"{warn_times}",
                f"{warn_causes}",
                f"{warn_names}",
                f"{warn_dates}",
                chat_id,
                id,
            ):
                await conn.execute(
                    "insert into warn (uid, chat_id, warns, last_warns_times, last_warns_causes, last_warns_names, "
                    "last_warns_dates) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                    id,
                    chat_id,
                    warns,
                    f"{warn_times}",
                    f"{warn_causes}",
                    f"{warn_names}",
                    f"{warn_dates}",
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
        u_acc = await get_user_access_level(uid, chat_id)
        if u_acc <= await get_user_access_level(id, chat_id) or not await haveAccess(
            "gunwarn", chat_id, uid
        ):
            continue
        ch_warns = await get_user_warns(id, chat_id)
        if ch_warns == 0:
            continue
        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update warn set warns = $1 where chat_id=$2 and uid=$3 returning 1",
                ch_warns - 1,
                chat_id,
                id,
            ):
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
        u_acc = await get_user_access_level(uid, chat_id)
        if (
            u_acc <= await get_user_access_level(id, chat_id) and uid != id
        ) or not await haveAccess("gsnick", chat_id, uid):
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
        u_acc = await get_user_access_level(uid, chat_id)
        ch_nickname = await get_user_nickname(id, chat_id)
        if (
            (u_acc <= await get_user_access_level(id, chat_id) and uid != id)
            or not await haveAccess("grnick", chat_id, uid)
            or ch_nickname is None
        ):
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
                    peer_id=chat_id + 2000000000, fields=['deactivated']  # type: ignore
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
