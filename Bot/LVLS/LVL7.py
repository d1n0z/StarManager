import re

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import (
    getUserPremium,
    getUserName,
    getUserNickname,
    getChatName,
    getUserAccessLevel,
    getIDFromMessage,
    getgpool,
    getUserLeague,
    editMessage,
    messagereply,
)
from config.config import COMMANDS, LVL_NAMES, CREATEGROUPLEAGUES
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD("async"))
async def asynch(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        if await conn.fetchval(
            "select exists(select 1 from gpool where uid=$1 and chat_id=$2)",
            uid,
            chat_id,
        ):
            return await messagereply(
                message, disable_mentions=1, message=messages.async_already_bound()
            )
        bound = await conn.fetchval("select count(*) as c from gpool where uid=$1", uid)
        u_premium = (
            True
            if await conn.fetchval(
                "select exists(select 1 from premium where uid=$1)", uid
            )
            else False
        )
        if (not u_premium and bound >= 30) or (u_premium and bound >= 100):
            return await messagereply(
                message, disable_mentions=1, message=messages.async_limit()
            )
        await conn.execute(
            "insert into gpool (uid, chat_id) values ($1, $2)", uid, chat_id
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.async_done(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id)
        ),
    )


@bl.chat_message(SearchCMD("delasync"))
async def delasync(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) == 2 and data[1].isdigit():
        delchid = int(data[1])
    else:
        delchid = chat_id
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "delete from gpool where uid=$1 and chat_id=$2 returning 1", uid, delchid
        ):
            return await messagereply(
                message, disable_mentions=1, message=messages.delasync_already_unbound()
            )
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.delasync_done(
            uid,
            await getUserName(uid),
            await getUserNickname(uid, chat_id),
            await getChatName(delchid),
        ),
    )


@bl.chat_message(SearchCMD("creategroup"))
async def creategroup(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=messages.creategroup_hint()
        )
    group_name = "".join(data[1:])
    pattern = re.compile(r"[a-zA-Z0-9]")
    if len(pattern.findall(group_name)) != len(group_name) or len(group_name) > 16:
        return await messagereply(
            message, disable_mentions=1, message=messages.creategroup_incorrect_name()
        )
    uid = message.from_id
    u_premium = await getUserPremium(uid)
    limit = CREATEGROUPLEAGUES[await getUserLeague(uid) - 1] if not u_premium else 12
    async with (await pool()).acquire() as conn:
        if (
            len(
                set(
                    i[0]
                    for i in await conn.fetch(
                        'select "group" from chatgroups where uid=$1', uid
                    )
                )
            )
            >= limit
        ):
            return await messagereply(
                message, disable_mentions=1, message=messages.creategroup_premium()
            )
        if await conn.fetchval(
            'select exists(select 1 from chatgroups where uid=$1 and "group"=$2)',
            uid,
            group_name,
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=messages.creategroup_already_created(group_name),
            )
        await conn.execute(
            'insert into chatgroups (uid, "group", chat_id) values ($1, $2, $3)',
            uid,
            group_name,
            chat_id,
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.creategroup_done(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), group_name
        ),
    )


@bl.chat_message(SearchCMD("bind"))
async def bind(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=messages.bind_hint()
        )
    group_name = " ".join(data[1:])
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            'select exists(select 1 from chatgroups where uid=$1 and "group"=$2)',
            uid,
            group_name,
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=messages.bind_group_not_found(group_name),
            )
        if await conn.fetchval(
            'select exists(select 1 from chatgroups where "group"=$1 and chat_id=$2)',
            group_name,
            chat_id,
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=messages.bind_chat_already_bound(group_name),
            )
        await conn.execute(
            'insert into chatgroups (uid, "group", chat_id) values ($1, $2, $3)',
            uid,
            group_name,
            chat_id,
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.bind(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), group_name
        ),
    )


@bl.chat_message(SearchCMD("unbind"))
async def unbind(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=messages.unbind_hint()
        )
    group_name = " ".join(data[1:])
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            'select exists(select 1 from chatgroups where "group"=$1)', group_name
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=messages.unbind_group_not_found(group_name),
            )
        if not await conn.fetchval(
            'delete from chatgroups where "group"=$1 and chat_id=$2 returning 1',
            group_name,
            chat_id,
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=messages.unbind_chat_already_unbound(group_name),
            )
    uid = message.from_id
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.unbind(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), group_name
        ),
    )


@bl.chat_message(SearchCMD("bindlist"))
async def bindlist(message: Message):
    data = message.text.split()
    if len(data) == 1:
        return await messagereply(
            message, disable_mentions=1, message=messages.bindlist_hint()
        )
    group_name = " ".join(data[1:])
    async with (await pool()).acquire() as conn:
        if not (
            group := await conn.fetch(
                'select "chat_id" from chatgroups where uid=$1 and "group"=$2 order by '
                "chat_id",
                message.from_id,
                group_name,
            )
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=messages.bind_group_not_found(group_name),
            )
    await messagereply(
        message,
        disable_mentions=1,
        keyboard=keyboard.bindlist(message.from_id, group_name, 0, len(group)),
        message=messages.bindlist(
            group_name, [(i[0], await getChatName(i[0])) for i in group[:15]]
        ),
    )


@bl.chat_message(SearchCMD("delgroup"))
async def delgroup(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=messages.delgroup_hint()
        )
    group_name = " ".join(data[1:])
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            'delete from chatgroups where "group"=$1 and uid=$2 returning 1',
            group_name,
            uid,
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=messages.delgroup_not_found(group_name),
            )
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.delgroup(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), group_name
        ),
    )


@bl.chat_message(SearchCMD("mygroups"))
async def mygroups(message: Message):
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        groups = [
            i[0]
            for i in await conn.fetch(
                'select "group" from chatgroups where uid=$1 order by id desc', uid
            )
        ]
        groups = {
            i: await conn.fetchval(
                'select count(*) as c from chatgroups where "group"=$1 and uid=$2',
                i,
                uid,
            )
            for i in list(set(groups))
        }
    if len(groups) <= 0:
        return await messagereply(
            message, disable_mentions=1, message=messages.mygroups_no_groups()
        )
    msg = f"🟣 Список ваших групп (Всего: {len(groups)})\n\n"
    for k, (group, count) in enumerate(groups.items()):
        msg += f"➖ {k + 1} | {group} | Количество бесед : {count}\n"
    await messagereply(message, disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD("filteradd"))
async def filteradd(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=messages.filteradd_hint()
        )
    word = " ".join(data[1:])
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        if await conn.fetchval(
            "select exists(select 1 from filterexceptions where owner_id=$1 and chat_id=$2 and "
            "filter=$3)",
            uid,
            chat_id,
            word,
        ):
            await conn.execute(
                "delete from filterexceptions where owner_id=$1 and chat_id=$2 and filter=$3",
                uid,
                chat_id,
                word,
            )
            id = None
        elif await conn.fetchval(
            "select exists(select 1 from filters where (chat_id=$1 or (owner_id=$2 and exists("
            "select 1 from gpool where uid=$2 and chat_id=$1))) and filter=$3)",
            chat_id,
            uid,
            word,
        ):
            return await messagereply(
                message, disable_mentions=1, message=messages.filteradd_dup(word)
            )
        else:
            id = await conn.fetchval(
                "insert into filters (chat_id, filter) values ($1, $2) returning id",
                chat_id,
                word,
            )
    msg = messages.filteradd(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), word
    )
    await messagereply(
        message,
        disable_mentions=1,
        message=msg,
        keyboard=keyboard.filteradd(uid, id, msg) if id else None,
    )


@bl.chat_message(SearchCMD("filterdel"))
async def filterdel(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=messages.filterdel_hint()
        )
    word = " ".join(data[1:])
    uid, fid = message.from_id, None
    async with (await pool()).acquire() as conn:
        if fid := await conn.fetchval(
            "select id from filters where owner_id=$1 and filter=$2 and exists("
            "select 1 from gpool where uid=$1 and chat_id=$3)",
            uid,
            word,
            chat_id,
        ):
            await conn.execute(
                "insert into filterexceptions (owner_id, chat_id, filter) values ($1, $2, $3)",
                uid,
                chat_id,
                word,
            )
        elif not await conn.fetchval(
            "delete from filters where chat_id=$1 and filter=$2 returning 1",
            chat_id,
            word,
        ):
            return await messagereply(
                message, disable_mentions=1, message=messages.filterdel_not_found(word)
            )
    msg = messages.filterdel(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), word
    )
    await messagereply(
        message,
        disable_mentions=1,
        message=msg,
        keyboard=keyboard.filterdel(uid, fid, msg) if fid else None,
    )


@bl.chat_message(SearchCMD("filter"))
async def filter(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.filter(),
        keyboard=keyboard.filter(message.from_id),
    )


@bl.chat_message(SearchCMD("editlevel"))
async def editlevel(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if not await getUserPremium(uid):
        return await messagereply(
            message, disable_mentions=1, message=messages.editlvl_no_premium()
        )
    data = message.text.split()
    try:
        if len(data) != 3:
            raise ValueError
        command = data[1]
        given_lvl = int(data[2])
        if given_lvl not in range(0, 8):
            raise ValueError
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=messages.editlvl_hint()
        )
    if command not in COMMANDS or COMMANDS[command] not in range(0, 8):
        return await messagereply(
            message, disable_mentions=1, message=messages.editlvl_command_not_found()
        )
    async with (await pool()).acquire() as conn:
        bl = await conn.fetchrow(
            "select id, lvl from commandlevels where chat_id=$1 and cmd=$2",
            chat_id,
            command,
        )
        if bl:
            original_lvl = bl[1]
            if given_lvl == COMMANDS[command]:
                await conn.execute("delete from commandlevels where id=$1", bl[0])
            else:
                await conn.execute(
                    "update commandlevels set lvl = $1 where id=$2", given_lvl, bl[0]
                )
        else:
            original_lvl = COMMANDS[command]
            await conn.execute(
                "insert into commandlevels (chat_id, cmd, lvl) values ($1, $2, $3)",
                chat_id,
                command,
                given_lvl,
            )
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.editlvl(
            uid,
            await getUserName(uid),
            await getUserNickname(uid, chat_id),
            command,
            original_lvl,
            given_lvl,
        ),
    )


@bl.chat_message(SearchCMD("giveowner"))
async def giveowner(message: Message):
    chat_id = message.peer_id - 2000000000
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id or id < 0:
        return await messagereply(
            message, disable_mentions=1, message=messages.giveowner_hint()
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.giveowner_ask(),
        keyboard=keyboard.giveowner(chat_id, id, message.from_id),
    )


@bl.chat_message(SearchCMD("levelname"))
async def levelname(message: Message):
    chat_id = message.peer_id - 2000000000
    u_premium = await getUserPremium(message.from_id)
    if not u_premium:
        return await messagereply(
            message, disable_mentions=1, message=messages.no_prem()
        )

    data = message.text.split()
    try:
        lvl = int(data[1])
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=messages.levelname_hint()
        )

    if len(data) < 3 or lvl < 0 or lvl > 8:
        return await messagereply(
            message, disable_mentions=1, message=messages.levelname_hint()
        )

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update accessnames set name = $1 where chat_id=$2 and lvl=$3 returning 1",
            " ".join(data[2:]),
            chat_id,
            lvl,
        ):
            await conn.execute(
                "insert into accessnames (chat_id, lvl, name) values ($1, $2, $3)",
                chat_id,
                lvl,
                " ".join(data[2:]),
            )
    uid = message.from_id
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.levelname(
            uid,
            await getUserName(uid),
            await getUserNickname(uid, chat_id),
            lvl,
            " ".join(data[2:]),
        ),
    )


@bl.chat_message(SearchCMD("resetlevel"))
async def resetlevel(message: Message):
    chat_id = message.peer_id - 2000000000
    if not await getUserPremium(message.from_id):
        return await messagereply(
            message, disable_mentions=1, message=messages.no_prem()
        )

    data = message.text.split()
    try:
        lvl = int(data[1])
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=messages.resetlevel_hint()
        )

    if len(data) < 2 or lvl < 0 or lvl > 8:
        return await messagereply(
            message, disable_mentions=1, message=messages.resetlevel_hint()
        )

    async with (await pool()).acquire() as conn:
        await conn.execute(
            "update accessnames set name = $1 where chat_id=$2 and lvl=$3",
            LVL_NAMES[lvl],
            chat_id,
            lvl,
        )
    uid = message.from_id
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.levelname(
            uid,
            await getUserName(uid),
            await getUserNickname(uid, chat_id),
            lvl,
            LVL_NAMES[lvl],
        ),
    )


@bl.chat_message(SearchCMD("settings"))
async def settings(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.settings(),
        keyboard=keyboard.settings(message.from_id),
    )


@bl.chat_message(SearchCMD("listasync"))
async def listasync(message: Message):
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        chat_ids = [
            i[0]
            for i in await conn.fetch(
                "select chat_id from gpool where uid=$1 order by id desc", uid
            )
        ]
    total = len(chat_ids)
    chat_ids = chat_ids[:15]
    names = []
    if len(chat_ids) > 0:
        for i in chat_ids:
            names.append(await getChatName(i))
    chats_info = [{"id": i, "name": names[k]} for k, i in enumerate(chat_ids)]
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.listasync(chats_info, total),
        keyboard=keyboard.listasync(uid, total),
    )


@bl.chat_message(SearchCMD("import"))
async def import_(message: Message):
    data = message.text.split()
    if len(data) != 2 or not data[1].isdigit():
        return await messagereply(
            message, disable_mentions=1, message=messages.import_hint()
        )
    importchatid = int(data[1])
    if await getUserAccessLevel(message.from_id, importchatid) < 7:
        return await messagereply(
            message, disable_mentions=1, message=messages.import_notowner()
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=messages.import_(importchatid, await getChatName(importchatid)),
        keyboard=keyboard.import_(message.from_id, importchatid),
    )
