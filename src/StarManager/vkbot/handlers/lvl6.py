import time

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from StarManager.core import managers
from StarManager.core.config import api, settings
from StarManager.core.db import pool
from StarManager.core.utils import (
    edit_message,
    get_chat_access_name,
    get_gpool,
    get_pool,
    get_user_access_level,
    get_user_name,
    get_user_nickname,
    get_user_premium,
    is_higher,
    messagereply,
    search_id_in_message,
    set_chat_mute,
    set_user_access_level,
)
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.checkers import haveAccess
from StarManager.vkbot.rules import SearchCMD

bl = BotLabeler()


@bl.chat_message(SearchCMD("gdelaccess"))
async def gdelaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gdelaccess_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if uid == id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.delaccess_myself()
        )
    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    name = await get_user_name(id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gdelaccess_start(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            id,
            name,
            await get_user_nickname(id, chat_id),
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gdelaccess", chat_id, uid
        ):
            continue
        acc = (await managers.access_level.get(id, chat_id))
        if acc is None or acc.custom_level_name is None:
            await set_user_access_level(id, chat_id, 0)
            success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.gdelaccess(
            id,
            name,
            await get_user_nickname(id, edit.peer_id - 2000000000),
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("gsetaccess"))
async def gsetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if (len(data) <= 2 and message.reply_message is None) or (
        len(data) <= 1 and message.reply_message is not None
    ):
        return await messagereply(
            message, message=await messages.gsetaccess_hint(), disable_mentions=1
        )
    id = await search_id_in_message(message.text, message.reply_message)
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if uid == id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.setaccess_myself()
        )

    try:
        acc = int(data[-1])
        if acc <= 0 or acc >= 7 or not id:
            raise
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.gsetaccess_hint()
        )
    if not (chats := await get_gpool(chat_id)):
        return await messagereply(
            message, disable_mentions=1, message=await messages.chat_unbound()
        )

    name = await get_user_name(id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.gsetaccess_start(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            id,
            name,
            await get_user_nickname(id, chat_id),
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "gsetaccess", chat_id, uid
        ):
            continue
        acc = (await managers.access_level.get(id, chat_id))
        if acc is None or acc.custom_level_name is None:
            await set_user_access_level(id, chat_id, acc)
            success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.gsetaccess(
            id,
            name,
            await get_user_nickname(id, edit.peer_id - 2000000000),
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("demote"))
async def demote(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.demote_choose(),
        keyboard=keyboard.demote_choose(message.from_id, message.peer_id - 2000000000),
    )


@bl.chat_message(SearchCMD("ssetaccess"))
async def ssetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if (len(data) <= 3 and message.reply_message is None) or (
        len(data) <= 2 and message.reply_message is not None
    ):
        return await messagereply(
            message, message=await messages.ssetaccess_hint(), disable_mentions=1
        )
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if uid == id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.setaccess_myself()
        )

    try:
        acc = int(data[-1])
        if acc <= 0 or acc >= 7 or not id:
            raise
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.setacc_hint()
        )

    if not (chats := await get_pool(chat_id, data[1])):
        return await messagereply(
            message, disable_mentions=1, message=await messages.s_invalid_group(data[1])
        )

    name = await get_user_name(id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.ssetaccess_start(
            uid,
            await get_user_name(uid),
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
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "ssetaccess", chat_id, uid
        ):
            continue
        acc = (await managers.access_level.get(id, chat_id))
        if acc is None or acc.custom_level_name is None:
            await set_user_access_level(id, chat_id, acc)
            success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.ssetaccess(
            id,
            name,
            await get_user_nickname(id, edit.peer_id - 2000000000),
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("sdelaccess"))
async def sdelaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if (len(data) <= 2 and message.reply_message is None) or (
        len(data) <= 1 and message.reply_message is not None
    ):
        return await messagereply(
            message, message=await messages.sdelaccess_hint(), disable_mentions=1
        )
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.sdelaccess_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if uid == id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.delaccess_myself()
        )
    if not (chats := await get_pool(chat_id, data[1])):
        return await messagereply(
            message, disable_mentions=1, message=await messages.s_invalid_group(data[1])
        )
    name = await get_user_name(id)
    edit = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.sdelaccess_start(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            id,
            name,
            await get_user_nickname(id, chat_id),
            data[1],
            len(chats),
        ),
    )
    success = 0
    for chat_id in chats:
        if not await is_higher(uid, id, chat_id) or not await haveAccess(
            "sdelaccess", chat_id, uid
        ):
            continue
        acc = (await managers.access_level.get(id, chat_id))
        if acc is None or acc.custom_level_name is None:
            await set_user_access_level(id, chat_id, 0)
            success += 1

    if edit is None:
        return
    await api.messages.edit(
        peer_id=edit.peer_id,
        conversation_message_id=edit.conversation_message_id,
        message=await messages.sdelaccess(
            id,
            name,
            await get_user_nickname(id, edit.peer_id - 2000000000),
            len(chats),
            success,
        ),
    )


@bl.chat_message(SearchCMD("ignore"))
async def ignore(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await get_user_premium(uid)
    if not u_prem:
        return await messagereply(
            message, disable_mentions=1, message=await messages.no_prem()
        )
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.ignore_hint()
        )
    if await get_user_access_level(uid, chat_id) <= await get_user_access_level(
        id, chat_id
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.ignore_higher()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "select exists(select 1 from ignore where chat_id=$1 and uid=$2)",
            chat_id,
            id,
        ):
            await conn.execute(
                "insert into ignore (chat_id, uid) values ($1, $2)", chat_id, id
            )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.ignore(
            id, await get_user_name(id), await get_user_nickname(uid, chat_id)
        ),
    )


@bl.chat_message(SearchCMD("unignore"))
async def unignore(message: Message):
    uid = message.from_id
    if not await get_user_premium(uid):
        return await messagereply(
            message, disable_mentions=1, message=await messages.no_prem()
        )
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.ignore_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    chat_id = message.peer_id - 2000000000
    name = await get_user_name(id)
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "delete from ignore where chat_id=$1 and uid=$2 returning 1", chat_id, id
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.unignore_not_ignored(),
            )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.unignore(
            id, name, await get_user_nickname(uid, chat_id)
        ),
    )


@bl.chat_message(SearchCMD("ignorelist"))
async def ignorelist(message: Message):
    if int(await get_user_premium(message.from_id)) <= 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.no_prem()
        )
    async with (await pool()).acquire() as conn:
        ids = [
            i[0]
            for i in await conn.fetch(
                "select uid from ignore where chat_id=$1", message.peer_id - 2000000000
            )
        ]
    raw_names = await api.users.get(user_ids=ids)
    names = []
    for i in raw_names:
        names.append(f"{i.first_name} {i.last_name}")
    await messagereply(
        message, disable_mentions=1, message=await messages.ignorelist(ids, names)
    )


@bl.chat_message(SearchCMD("chatlimit"))
async def chatlimit(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if not await get_user_premium(uid):
        return await messagereply(
            message, disable_mentions=1, message=await messages.no_prem()
        )
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.chatlimit_hint()
        )

    t = data[1]
    pfx = t[-1]
    if t != "0":
        if not t[:-1].isdigit() or pfx not in ["s", "m", "h"]:
            return await messagereply(
                message, disable_mentions=1, message=await messages.chatlimit_hint()
            )
        st = int(t[:-1])
        tst = int(st)
        if pfx == "m":
            st *= 60
        elif pfx == "h":
            st *= 60 * 60
    else:
        st = 0
        tst = 0

    async with (await pool()).acquire() as conn:
        chlim = await conn.fetchval(
            "select time from chatlimit where chat_id=$1", chat_id
        )
        lpos = chlim or 1
        if chlim is not None:
            await conn.execute(
                "update chatlimit set time = $1 where chat_id=$2", st, chat_id
            )
        else:
            await conn.execute(
                "insert into chatlimit (chat_id, time) values ($1, $2)", chat_id, st
            )

    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.chatlimit(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            tst,
            pfx,
            lpos,
        ),
    )


@bl.chat_message(SearchCMD("resetnick"))
async def resetnick(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.resetnick_yon(),
        keyboard=keyboard.resetnick_accept(
            message.from_id, message.peer_id - 2000000000
        ),
    )


@bl.chat_message(SearchCMD("resetaccess"))
async def resetaccess(message: Message):
    data = message.text.split()
    if len(data) != 2 or not data[1].isdigit() or int(data[1]) < 1 or int(data[1]) > 6:
        return await messagereply(
            message, disable_mentions=1, message=await messages.resetaccess_hint()
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.resetaccess_yon(
            await get_chat_access_name(message.chat_id, int(data[1]))
            or settings.lvl_names[int(data[1])]
        ),
        keyboard=keyboard.resetaccess_accept(
            message.from_id, message.peer_id - 2000000000, data[1]
        ),
    )


@bl.chat_message(SearchCMD("notif"))
async def notif(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) >= 2:
        name = " ".join(data[1:])
        async with (await pool()).acquire() as conn:
            notif = await conn.fetchval(
                "select count(*) as c from notifications where chat_id=$1 and name=$2",
                chat_id,
                name,
            )
            if not notif:
                await conn.execute(
                    "insert into notifications (chat_id, tag, every, status, time, name, description, text) "
                    "values ($1, 1, -1, 1, $2, $3, '', '')",
                    chat_id,
                    time.time() - 5,
                    name,
                )
                return await messagereply(
                    message,
                    disable_mentions=1,
                    message=await messages.notification(
                        name, "", time.time(), -1, 1, 1
                    ),
                    keyboard=keyboard.notification(uid, 1, name),
                )
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.notif_already_exist(name),
        )
    async with (await pool()).acquire() as conn:
        activenotifs = await conn.fetchval(
            "select count(*) as c from notifications where chat_id=$1 and status=1",
            chat_id,
        )
        notifs = await conn.fetchval(
            "select count(*) as c from notifications where chat_id=$1", chat_id
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.notif(notifs, activenotifs),
        keyboard=keyboard.notif(uid),
    )


@bl.chat_message(SearchCMD("purge"))
async def purge(message: Message):
    chat_id = message.peer_id - 2000000000
    edit = await messagereply(
        message, disable_mentions=1, message=await messages.purge_start()
    )
    users = [
        i.member_id
        for i in (
            await api.messages.get_conversation_members(peer_id=message.peer_id)
        ).items
    ]
    dtdnicknames = 0
    dtdaccesslevels = 0
    async with (await pool()).acquire() as conn:
        for i in await conn.fetch(
            "select id, uid from nickname where chat_id=$1", chat_id
        ):
            if i[1] not in users:
                await conn.execute("delete from nickname where id=$1", i[0])
                dtdnicknames += 1
    for i in await managers.access_level.get_all(chat_id=chat_id):
        if i.uid not in users:
            await managers.access_level.delete_row(i)
            await set_chat_mute(i.uid, chat_id, 0)
            dtdaccesslevels += 1

    if edit is None:
        return
    await edit_message(
        await messages.purge(dtdnicknames, dtdaccesslevels)
        if dtdnicknames > 0 or dtdaccesslevels > 0
        else await messages.purge_empty(),
        message.peer_id,
        edit.conversation_message_id,
    )


@bl.chat_message(SearchCMD("rename"))
async def rename(message: Message):
    data = message.text.split()
    if len(data) < 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.rename_hint()
        )
    if len(" ".join(data[1:])) >= 100:
        return await messagereply(
            message, disable_mentions=1, message=await messages.rename_toolong()
        )
    chat_id = message.chat_id
    try:
        await api.messages.edit_chat(chat_id, " ".join(data[1:]))
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.rename_error()
        )
    async with (await pool()).acquire() as conn:
        await conn.execute("delete from chatnames where chat_id=$1", chat_id)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.rename(
            message.from_id,
            await get_user_name(message.from_id),
            await get_user_nickname(message.from_id, chat_id),
        ),
    )


@bl.chat_message(SearchCMD("raid"))
async def raid(message: Message):
    async with (await pool()).acquire() as conn:
        status = await conn.fetchval(
            "select status from raidmode where chat_id=$1", message.peer_id - 2000000000
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.raid(),
        keyboard=keyboard.raid(message.from_id, status),
    )
