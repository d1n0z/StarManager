import re

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import getUserPremium, getUserName, getUserNickname, getChatName, getUserAccessLevel, getIDFromMessage, \
    getgpool, getUserLeague
from config.config import api, COMMANDS, LVL_NAMES, CREATEGROUPLEAGUES
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('async'))
async def asynch(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if await (await c.execute('select id from gpool where uid=%s and chat_id=%s', (uid, chat_id))).fetchone():
                return await message.reply(disable_mentions=1, message=messages.async_already_bound())
            bound = (await (await c.execute('select count(*) as c from gpool where uid=%s', (uid,))).fetchone())[0]
            u_premium = True if await (await c.execute(
                'select id from premium where uid=%s', (uid,))).fetchone() else False
            if (not u_premium and bound >= 30) or (u_premium and bound >= 100):
                return await message.reply(disable_mentions=1, message=messages.async_limit())
            await c.execute('insert into gpool (uid, chat_id) values (%s, %s)', (uid, chat_id))
            await conn.commit()
    await message.reply(disable_mentions=1, message=messages.async_done(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id)))


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
            if not (await c.execute('delete from gpool where uid=%s and chat_id=%s', (uid, delchid))).rowcount:
                return await message.reply(disable_mentions=1, message=messages.delasync_already_unbound())
            await conn.commit()
    await message.reply(disable_mentions=1, message=messages.delasync_done(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), await getChatName(delchid)))


@bl.chat_message(SearchCMD('creategroup'))
async def creategroup(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.creategroup_hint())
    group_name = ''.join(data[1:])
    pattern = re.compile(r"[a-zA-Z0-9]")
    if len(pattern.findall(group_name)) != len(group_name) or len(group_name) > 16:
        return await message.reply(disable_mentions=1, message=messages.creategroup_incorrect_name())
    uid = message.from_id
    u_premium = await getUserPremium(uid)
    limit = CREATEGROUPLEAGUES[await getUserLeague(uid) - 1] if not u_premium else 12
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if len(set(i[0] for i in await (await c.execute(
                    'select "group" from chatgroups where uid=%s', (uid,))).fetchall())) >= limit:
                return await message.reply(disable_mentions=1, message=messages.creategroup_premium())
            if await (await c.execute('select id from chatgroups where uid=%s and "group"=%s',
                                      (uid, group_name))).fetchone():
                return await message.reply(disable_mentions=1, message=messages.creategroup_already_created(group_name))
            await c.execute('insert into chatgroups (uid, "group", chat_id) values (%s, %s, %s)',
                            (uid, group_name, chat_id))
            await conn.commit()
    await message.reply(disable_mentions=1, message=messages.creategroup_done(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), group_name))


@bl.chat_message(SearchCMD('bind'))
async def bind(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.bind_hint())
    group_name = ' '.join(data[1:])
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not await (await c.execute('select id from chatgroups where uid=%s and "group"=%s',
                                          (uid, group_name))).fetchone():
                return await message.reply(disable_mentions=1, message=messages.bind_group_not_found(group_name))
            if await (await c.execute('select id from chatgroups where "group"=%s and chat_id=%s',
                                      (group_name, chat_id))).fetchone():
                return await message.reply(disable_mentions=1, message=messages.bind_chat_already_bound(group_name))
            await c.execute('insert into chatgroups (uid, "group", chat_id) values (%s, %s, %s)',
                            (uid, group_name, chat_id))
            await conn.commit()
    await message.reply(disable_mentions=1, message=messages.bind(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), group_name))


@bl.chat_message(SearchCMD('unbind'))
async def unbind(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.unbind_hint())
    group_name = ' '.join(data[1:])
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not await (await c.execute('select id from chatgroups where "group"=%s', (group_name,))).fetchone():
                return await message.reply(disable_mentions=1, message=messages.unbind_group_not_found(group_name))
            if not (await c.execute(
                    'delete from chatgroups where "group"=%s and chat_id=%s', (group_name, chat_id))).rowcount:
                return await message.reply(disable_mentions=1, message=messages.unbind_chat_already_unbound(group_name))
            await conn.commit()
    uid = message.from_id
    await message.reply(disable_mentions=1, message=messages.unbind(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), group_name))


@bl.chat_message(SearchCMD('delgroup'))
async def delgroup(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.delgroup_hint())
    group_name = ' '.join(data[1:])
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from chatgroups where "group"=%s and uid=%s', (group_name, uid))).rowcount:
                return await message.reply(disable_mentions=1, message=messages.delgroup_not_found(group_name))
            await conn.commit()
    await message.reply(disable_mentions=1, message=messages.delgroup(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), group_name))


@bl.chat_message(SearchCMD('mygroups'))
async def mygroups(message: Message):
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            groups = [i[0] for i in await (await c.execute(
                'select "group" from chatgroups where uid=%s order by id desc', (uid,))).fetchall()]
            groups = {i: (await (await c.execute(
                'select count(*) as c from chatgroups where "group"=%s and uid=%s',
                (i, uid))).fetchone())[0] for i in list(set(groups))}
    if len(groups) <= 0:
        return await message.reply(disable_mentions=1, message=messages.mygroups_no_groups())
    msg = f'🟣 Список ваших групп (Всего: {len(groups)})\n\n'
    for k, (group, count) in enumerate(groups.items()):
        msg += f'➖ {k + 1} | {group} | Количество бесед : {count}\n'
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('addfilter'))
async def addfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.addfilter_hint())
    addfilter = ' '.join(data[1:])
    uid = message.from_id
    u_name = await getUserName(uid)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not await (await c.execute(
                    'select id from filters where chat_id=%s and filter=%s', (chat_id, addfilter))).fetchone():
                await c.execute('insert into filters (chat_id, filter) values (%s, %s)', (chat_id, addfilter))
                await conn.commit()
    await message.reply(disable_mentions=1, message=messages.addfilter(
        uid, u_name, await getUserNickname(uid, chat_id)))


@bl.chat_message(SearchCMD('delfilter'))
async def delfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.delfilter_hint())
    delfilter = ' '.join(data[1:])
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from filters where chat_id=%s and filter=%s',
                                    (chat_id, delfilter))).rowcount:
                return await message.reply(disable_mentions=1, message=messages.delfilter_no_filter())
            await conn.commit()
    uid = message.from_id
    await message.reply(disable_mentions=1, message=messages.delfilter(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id)))


@bl.chat_message(SearchCMD('filterlist'))
async def filterlist(message: Message):
    chat_id = message.peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            filters = await (await c.execute('select filter from filters where chat_id=%s', (chat_id,))).fetchall()
    if len(filters) == 0:
        return await message.reply(
            disable_mentions=1,
            message='⚠ В данной беседе отсутствуют запрещённые слова, вы можете добавить используя /addfilter')
    msg = f'🟣 Список запрещенных слов (Всего : {len(filters)})\n\n➖ Полный список : '
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
        return await message.reply(disable_mentions=1, message=messages.gaddfilter_hint())

    if not (chats := await getgpool(chat_id)):
        return await message.reply(disable_mentions=1, message=messages.chat_unbound())

    uid = message.from_id
    if len(chats) == 0:
        return await message.reply(disable_mentions=1, message=messages.chat_unbound())
    msg = messages.gaddfilter_start(uid, await getUserName(uid), await getUserNickname(uid, chat_id), len(chats))
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
    await api.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.message_id, message=messages.gaddfilter(
        uid, await getUserName(uid), len(chats), success))


@bl.chat_message(SearchCMD('gdelfilter'))
async def gdelfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.gdelfilter_hint())
    if not (chats := await getgpool(chat_id)):
        return await message.reply(disable_mentions=1, message=messages.chat_unbound())

    uid = message.from_id
    if len(chats) == 0:
        return await message.reply(disable_mentions=1, message=messages.chat_unbound())
    edit = await message.reply(disable_mentions=1, message=messages.gdelfilter_start(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), len(chats)))
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
    await api.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.message_id,
                            message=messages.gdelfilter(uid, await getUserName(uid), len(chats), success))


@bl.chat_message(SearchCMD('editlevel'))
async def editlevel(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if not await getUserPremium(uid):
        return await message.reply(disable_mentions=1, message=messages.editlvl_no_premium())
    data = message.text.split()
    try:
        if len(data) != 3:
            raise ValueError
        command = data[1]
        given_lvl = int(data[2])
        if given_lvl not in range(0, 8):
            raise ValueError
    except:
        return await message.reply(disable_mentions=1, message=messages.editlvl_hint())
    if command not in COMMANDS or COMMANDS[command] not in range(0, 8):
        return await message.reply(disable_mentions=1, message=messages.editlvl_command_not_found())
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
    await message.reply(disable_mentions=1, message=messages.editlvl(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), command, original_lvl, given_lvl))


@bl.chat_message(SearchCMD('giveowner'))
async def giveowner(message: Message):
    chat_id = message.peer_id - 2000000000
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id or id < 0:
        return await message.reply(disable_mentions=1, message=messages.giveowner_hint())
    await message.reply(disable_mentions=1, message=messages.giveowner_ask(),
                        keyboard=keyboard.giveowner(chat_id, id, message.from_id))


@bl.chat_message(SearchCMD('levelname'))
async def levelname(message: Message):
    chat_id = message.peer_id - 2000000000
    u_premium = await getUserPremium(message.from_id)
    if not u_premium:
        return await message.reply(disable_mentions=1, message=messages.no_prem())

    data = message.text.split()
    try:
        lvl = int(data[1])
    except:
        return await message.reply(disable_mentions=1, message=messages.levelname_hint())

    if len(data) < 3 or lvl < 0 or lvl > 8:
        return await message.reply(disable_mentions=1, message=messages.levelname_hint())

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update accessnames set name = %s where chat_id=%s and lvl=%s',
                                    (' '.join(data[2:]), chat_id, lvl))).rowcount:
                await c.execute('insert into accessnames (chat_id, lvl, name) values (%s, %s, %s)',
                                (chat_id, lvl, ' '.join(data[2:])))
            await conn.commit()
    uid = message.from_id
    await message.reply(disable_mentions=1, message=messages.levelname(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), lvl, ' '.join(data[2:])))


@bl.chat_message(SearchCMD('resetlevel'))
async def resetlevel(message: Message):
    chat_id = message.peer_id - 2000000000
    if not await getUserPremium(message.from_id):
        return await message.reply(disable_mentions=1, message=messages.no_prem())

    data = message.text.split()
    try:
        lvl = int(data[1])
    except:
        return await message.reply(disable_mentions=1, message=messages.resetlevel_hint())

    if len(data) < 2 or lvl < 0 or lvl > 8:
        return await message.reply(disable_mentions=1, message=messages.resetlevel_hint())

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('update accessnames set name = %s where chat_id=%s and lvl=%s',
                            (LVL_NAMES[lvl], chat_id, lvl))
            await conn.commit()
    uid = message.from_id
    await message.reply(disable_mentions=1, message=messages.levelname(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), lvl, LVL_NAMES[lvl]))


@bl.chat_message(SearchCMD('settings'))
async def settings(message: Message):
    await message.reply(disable_mentions=1, message=messages.settings(), keyboard=keyboard.settings(message.from_id))


@bl.chat_message(SearchCMD('listasync'))
async def listasync(message: Message):
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chat_ids = [i[0] for i in await (await c.execute('select chat_id from gpool where uid=%s order by id desc',
                                                             (uid,))).fetchall()]
    total = len(chat_ids)
    chat_ids = chat_ids[:15]
    names = []
    if len(chat_ids) > 0:
        for i in chat_ids:
            names.append(await getChatName(i))
    chats_info = [{"id": i, "name": names[k]} for k, i in enumerate(chat_ids)]
    await message.reply(disable_mentions=1, message=messages.listasync(chats_info, total),
                        keyboard=keyboard.listasync(uid, total))


@bl.chat_message(SearchCMD('import'))
async def import_(message: Message):
    data = message.text.split()
    if len(data) != 2 or not data[1].isdigit():
        return await message.reply(disable_mentions=1, message=messages.import_hint())
    importchatid = int(data[1])
    if await getUserAccessLevel(message.from_id, importchatid) < 7:
        return await message.reply(disable_mentions=1, message=messages.import_notowner())
    await message.reply(disable_mentions=1, message=messages.import_(
        importchatid, await getChatName(importchatid)), keyboard=keyboard.import_(message.from_id, importchatid))
