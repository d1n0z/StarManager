import re

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import getUserPremium, getUserName, getUserNickname, getChatName, getUserAccessLevel, getIDFromMessage, \
    getgpool
from config.config import API, COMMANDS, LVL_NAMES
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('async'))
async def asynch(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if await (await c.execute('select id from gpool where uid=%s and chat_id=%s', (uid, chat_id))).fetchone():
                msg = messages.async_already_bound()
                await message.reply(disable_mentions=1, message=msg)
                return
            bound = (await (await c.execute('select count(*) as c from gpool where uid=%s', (uid,))).fetchone())[0]
            u_premium = True if await (await c.execute(
                'select id from premium where uid=%s', (uid,))).fetchone() else False
            if (not u_premium and bound >= 30) or (u_premium and bound >= 100):
                msg = messages.async_limit()
                await message.reply(disable_mentions=1, message=msg)
                return
            await c.execute('insert into gpool (uid, chat_id) values (%s, %s)', (uid, chat_id))
            await conn.commit()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.async_done(uid, u_name, u_nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('delasync'))
async def delasync(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) == 2 and data[1].isdigit():
        delchid = int(data[1])
    else:
        delchid = chat_id
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from gpool where uid=%s and chat_id=%s', (uid, chat_id))).rowcount:
                msg = messages.delasync_already_unbound()
                await message.reply(disable_mentions=1, message=msg)
                return
            await conn.commit()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    chat_name = await getChatName(delchid)
    msg = messages.delasync_done(uid, u_name, u_nickname, chat_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('creategroup'))
async def creategroup(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.creategroup_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    group_name = message.text[13:]
    pattern = re.compile(r"[a-zA-Z0-9]")
    if len(pattern.findall(group_name)) != len(group_name) or len(group_name) > 16:
        msg = messages.creategroup_incorrect_name()
        await message.reply(disable_mentions=1, message=msg)
        return

    uid = message.from_id
    u_premium = await getUserPremium(uid)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not u_premium and len(set(i[0] for i in await (
                    await c.execute('select "group" from chatgroups where uid=%s', (uid,))).fetchall())) >= 5:
                msg = messages.creategroup_premium()
                await message.reply(disable_mentions=1, message=msg)
                return
            if await (await c.execute('select id from chatgroups where uid=%s and "group"=%s',
                                      (uid, group_name))).fetchone():
                msg = messages.creategroup_already_created(group_name)
                await message.reply(disable_mentions=1, message=msg)
                return
            await c.execute('insert into chatgroups (uid, "group", chat_id) values (%s, %s, %s)',
                            (uid, group_name, chat_id))
            await conn.commit()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.creategroup_done(uid, u_name, u_nickname, group_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('bind'))
async def bind(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.bind_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    group_name = ' '.join(data[1:])
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not await (await c.execute('select id from chatgroups where uid=%s and "group"=%s',
                                          (uid, group_name))).fetchone():
                msg = messages.bind_group_not_found(group_name)
                await message.reply(disable_mentions=1, message=msg)
                return
            if await (await c.execute('select id from chatgroups where "group"=%s and chat_id=%s',
                                      (group_name, chat_id))).fetchone():
                msg = messages.bind_chat_already_bound(group_name)
                await message.reply(disable_mentions=1, message=msg)
                return
            await c.execute('insert into chatgroups (uid, "group", chat_id) values (%s, %s, %s)',
                            (uid, group_name, chat_id))
            await conn.commit()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.bind(uid, u_name, u_nickname, group_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('unbind'))
async def unbind(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.unbind_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    group_name = message.text[8:]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not await (await c.execute('select id from chatgroups where "group"=%s', (group_name,))).fetchone():
                msg = messages.unbind_group_not_found(group_name)
                await message.reply(disable_mentions=1, message=msg)
                return
            if not await (await c.execute('delete from chatgroups where "group"=%s and chat_id=%s',
                                          (group_name, chat_id))).rowcount:
                msg = messages.unbind_chat_already_unbound(group_name)
                await message.reply(disable_mentions=1, message=msg)
                return
            await conn.commit()

    uid = message.from_id
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.unbind(uid, u_name, u_nickname, group_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('delgroup'))
async def delgroup(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.delgroup_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    group_name = message.text[10:]

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from chatgroups where "group"=%s and uid=%s', (group_name, uid))).rowcount:
                msg = messages.delgroup_not_found(group_name)
                await message.reply(disable_mentions=1, message=msg)
                return
            await conn.commit()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.delgroup(uid, u_name, u_nickname, group_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('mygroups'))
async def mygroups(message: Message):
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            groups = [i[0] for i in await (await c.execute(
                'select "group" from chatgroups where uid=%s', (uid,))).fetchall()]
            groups = {i: (await (await c.execute('select count(*) as c from chatgroups where "group"=%s and uid=%s',
                                                 (i, uid))).fetchone())[0] for i in list(set(groups))}
    if len(groups) <= 0:
        msg = messages.mygroups_no_groups()
        await message.reply(disable_mentions=1, message=msg)
        return
    msg = f'🟣 Список ваших групп (Всего: {len(groups)})\n\n'

    for k, (group, count) in enumerate(groups.items()):
        msg += f'➖ {k + 1} | {group} | Количество бесед : {count}\n'
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('addfilter'))
async def addfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        msg = messages.addfilter_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    addfilter = ' '.join(data[1:])
    uid = message.from_id
    u_name = await getUserName(uid)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not await (await c.execute(
                    'select id from filters where chat_id=%s and filter=%s', (chat_id, addfilter))).fetchone():
                await c.execute('insert into filters (chat_id, filter) values (%s, %s)', (chat_id, addfilter))
                await conn.commit()
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.addfilter(uid, u_name, u_nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('delfilter'))
async def delfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        msg = messages.delfilter_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    delfilter = ' '.join(data[1:])

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from filters where chat_id=%s and filter=%s',
                                    (chat_id, delfilter))).rowcount:
                msg = messages.delfilter_no_filter()
                await message.reply(disable_mentions=1, message=msg)
                return
            await conn.commit()
    uid = message.from_id
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.delfilter(uid, u_name, u_nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('filterlist'))
async def filterlist(message: Message):
    chat_id = message.peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            filters = await (await c.execute('select filter from filters where chat_id=%s', (chat_id,))).fetchall()
    if len(filters) == 0:
        msg = '⚠ В данной беседе отсутствуют запрещённые слова, вы можете добавить используя /addfilter'
    else:
        msg = f'🟣 Список запрещенных слов (Всего : {len(filters)})\n\n'
        msg += '➖ Полный список : '
        for ind, item in enumerate(filters):
            msg += f'{item[0]} '
            if ind + 1 != len(filters):
                msg += ', '
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('gaddfilter'))
async def gaddfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        msg = messages.gaddfilter_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getgpool(chat_id)):
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    uid = message.from_id
    name = await getUserName(uid)
    if len(chats) == 0:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return
    kicker_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.gaddfilter_start(uid, kicker_name, u_nickname, len(chats))
    edit = await message.reply(disable_mentions=1, message=msg)
    addfilter = ' '.join(data[1:])
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('gaddfilter', chat_id, u_acc):
            continue
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not await (await c.execute('select id from filters where chat_id=%s and filter=%s',
                                              (chat_id, addfilter))).fetchone():
                    await c.execute('insert into filters (chat_id, filter) values (%s, %s)', (chat_id, addfilter))
                    await conn.commit()
        success += 1

    msggkick = messages.gaddfilter(uid, name, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.message_id, message=msggkick)


@bl.chat_message(SearchCMD('gdelfilter'))
async def gdelfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        msg = messages.gdelfilter_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if not (chats := await getgpool(chat_id)):
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    uid = message.from_id
    name = await getUserName(uid)
    if len(chats) == 0:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return
    kicker_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.gdelfilter_start(uid, kicker_name, u_nickname, len(chats))
    edit = await message.reply(disable_mentions=1, message=msg)
    delfilter = ' '.join(data[1:])
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('grnick', chat_id, u_acc):
            continue
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('delete from filters where chat_id=%s and filter=%s', (chat_id, delfilter))
                await conn.commit()
        success += 1

    msggkick = messages.gdelfilter(uid, name, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.message_id, message=msggkick)


@bl.chat_message(SearchCMD('editlevel'))
async def editlevel(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_premium = await getUserPremium(uid)
    if not u_premium:
        msg = messages.editlvl_no_premium()
        await message.reply(disable_mentions=1, message=msg)
        return
    data = message.text.split()
    if len(data) != 3:
        msg = messages.editlvl_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    try:
        command = data[1]
        given_lvl = int(data[2])
    except:
        msg = messages.editlvl_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if command not in COMMANDS or COMMANDS[command] not in range(0, 8):
        msg = messages.editlvl_command_not_found()
        await message.reply(disable_mentions=1, message=msg)
        return
    if given_lvl not in range(0, 8):
        msg = messages.editlvl_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            bl = await (await c.execute(
                'select id, lvl from commandlevels where chat_id=%s and cmd=%s', (chat_id, command))).fetchone()
            if bl:
                original_lvl = bl[1]
                await c.execute('update commandlevels set lvl = %s where id=%s', (given_lvl, bl[0]))
            else:
                original_lvl = COMMANDS[command]
                await c.execute('insert into commandlevels (chat_id, cmd, lvl) values (%s, %s, %s)',
                                (chat_id, command, given_lvl))
            await conn.commit()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.editlvl(uid, u_name, u_nickname, command, original_lvl, given_lvl)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('giveowner'))
async def giveowner(message: Message):
    chat_id = message.peer_id - 2000000000
    id = await getIDFromMessage(message.text, message.reply_message)
    if id is not None:
        kb = keyboard.giveowner(chat_id, id, message.from_id)
        msg = messages.giveowner_ask()
        await message.reply(disable_mentions=1, message=msg, keyboard=kb)
    else:
        msg = messages.giveowner_hint()
        await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('levelname'))
async def levelname(message: Message):
    chat_id = message.peer_id - 2000000000
    u_premium = await getUserPremium(message.from_id)
    if not u_premium:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    try:
        lvl = int(data[1])
    except:
        msg = messages.levelname_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if len(data) < 3 or lvl < 0 or lvl > 8:
        msg = messages.levelname_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update accessnames set name = %s where chat_id=%s and lvl=%s',
                                    (' '.join(data[2:]), chat_id, lvl))).rowcount:
                await c.execute('insert into accessnames (chat_id, lvl, name) values (%s, %s, %s)',
                                (chat_id, lvl, ' '.join(data[2:])))
            await conn.commit()
    uid = message.from_id
    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)

    msg = messages.levelname(uid, name, nick, lvl, ' '.join(data[2:]))
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('resetlevel'))
async def resetlevel(message: Message):
    chat_id = message.peer_id - 2000000000
    u_premium = await getUserPremium(message.from_id)
    if not u_premium:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    try:
        lvl = int(data[1])
    except:
        msg = messages.resetlevel_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if len(data) < 2 or lvl < 0 or lvl > 8:
        msg = messages.resetlevel_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('update accessnames set name = %s where chat_id=%s and lvl=%s',
                            (LVL_NAMES[lvl], chat_id, lvl))
            await conn.commit()

    uid = message.from_id
    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)

    msg = messages.levelname(uid, name, nick, lvl, LVL_NAMES[lvl])
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('settings'))
async def settings(message: Message):
    msg = messages.settings()
    kb = keyboard.settings(message.from_id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('listasync'))
async def listasync(message: Message):
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chat_ids = [i[0] for i in await (await c.execute('select chat_id from gpool where uid=%s',
                                                             (uid,))).fetchall()]
    total = len(chat_ids)
    chat_ids = chat_ids[:15]
    names = []
    if len(chat_ids) > 0:
        for i in chat_ids:
            names.append(await getChatName(i))
    chats_info = [{"id": i, "name": names[k]} for k, i in enumerate(chat_ids)]

    msg = messages.listasync(chats_info, total)
    kb = keyboard.listasync(uid, total)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)
