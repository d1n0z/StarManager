import time

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserName, getUserNickname, getUserAccessLevel, getUserPremium, editMessage, \
    getgpool, getpool, setUserAccessLevel, setChatMute
from config.config import api
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('gdelaccess'))
async def gdelaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.gdelaccess_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if uid == id:
        return await message.reply(disable_mentions=1, message=messages.delaccess_myself())
    if not (chats := await getgpool(chat_id)):
        return await message.reply(disable_mentions=1, message=messages.chat_unbound())

    name = await getUserName(id)
    edit = await message.reply(disable_mentions=1, message=messages.gdelaccess_start(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), id, name, await getUserNickname(id, chat_id),
        len(chats)))
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('gdelaccess', chat_id, u_acc) or await getUserAccessLevel(id, chat_id) >= u_acc:
            continue
        await setUserAccessLevel(id, chat_id, 0)
        success += 1
    await api.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=messages.gdelaccess(
                                id, name, await getUserNickname(id, edit.peer_id - 2000000000), len(chats), success))


@bl.chat_message(SearchCMD('gsetaccess'))
async def gsetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 2 and message.reply_message is None) or
            (len(data) <= 1 and message.reply_message is not None)):
        return await message.reply(message=messages.gsetaccess_hint(), disable_mentions=1)
    id = await getIDFromMessage(message.text, message.reply_message)
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if uid == id:
        return await message.reply(disable_mentions=1, message=messages.setaccess_myself())

    try:
        acc = int(data[-1])
        if acc <= 0 or acc >= 7 or not id:
            raise
    except:
        return await message.reply(disable_mentions=1, message=messages.gsetaccess_hint())
    if not (chats := await getgpool(chat_id)):
        return await message.reply(disable_mentions=1, message=messages.chat_unbound())

    name = await getUserName(id)
    edit = await message.reply(disable_mentions=1, message=messages.gsetaccess_start(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), id, name, await getUserNickname(id, chat_id),
        len(chats)))
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if acc >= u_acc or ch_acc >= u_acc or ch_acc >= acc or not await haveAccess('gsetaccess', chat_id, u_acc):
            continue
        await setUserAccessLevel(id, chat_id, acc)
        success += 1
    await api.messages.edit(
        peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
        message=messages.gsetaccess(id, name, await getUserNickname(id, edit.peer_id - 2000000000), len(chats), success)
    )


@bl.chat_message(SearchCMD('demote'))
async def demote(message: Message):
    await message.reply(disable_mentions=1, message=messages.demote_choose(),
                        keyboard=keyboard.demote_choose(message.from_id, message.peer_id - 2000000000))


@bl.chat_message(SearchCMD('ssetaccess'))
async def ssetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 3 and message.reply_message is None) or
            (len(data) <= 2 and message.reply_message is not None)):
        return await message.reply(message=messages.ssetaccess_hint(), disable_mentions=1)
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if uid == id:
        return await message.reply(disable_mentions=1, message=messages.setaccess_myself())

    try:
        acc = int(data[-1])
        if acc <= 0 or acc >= 7 or not id:
            raise
    except:
        return await message.reply(disable_mentions=1, message=messages.setacc_hint())

    if not (chats := await getpool(chat_id, data[1])):
        return await message.reply(disable_mentions=1, message=messages.s_invalid_group(data[1]))

    name = await getUserName(id)
    edit = await message.reply(disable_mentions=1, message=messages.ssetaccess_start(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), id, name,
        await getUserNickname(id, chat_id), len(chats), data[1]))
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if acc >= u_acc or ch_acc >= u_acc or ch_acc >= acc or not await haveAccess('ssetaccess', chat_id, u_acc):
            continue
        await setUserAccessLevel(id, chat_id, acc)
        success += 1

    await api.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=messages.ssetaccess(
                                id, name, await getUserNickname(id, edit.peer_id - 2000000000), len(chats), success))


@bl.chat_message(SearchCMD('sdelaccess'))
async def sdelaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 2 and message.reply_message is None) or
            (len(data) <= 1 and message.reply_message is not None)):
        return await message.reply(message=messages.sdelaccess_hint(), disable_mentions=1)
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.sdelaccess_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if uid == id:
        return await message.reply(disable_mentions=1, message=messages.delaccess_myself())
    if not (chats := await getpool(chat_id, data[1])):
        return await message.reply(disable_mentions=1, message=messages.s_invalid_group(data[1]))
    name = await getUserName(id)
    edit = await message.reply(disable_mentions=1, message=messages.sdelaccess_start(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), id, name,
        await getUserNickname(id, chat_id), data[1], len(chats)))
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('sdelaccess', chat_id, u_acc) or await getUserAccessLevel(id, chat_id) >= u_acc:
            continue
        await setUserAccessLevel(id, chat_id, 0)
        success += 1
    await api.messages.edit(
        peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=messages.sdelaccess(
            id, name, await getUserNickname(id, edit.peer_id - 2000000000), len(chats), success))


@bl.chat_message(SearchCMD('ignore'))
async def ignore(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        return await message.reply(disable_mentions=1, message=messages.no_prem())
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.ignore_hint())
    if await getUserAccessLevel(uid, chat_id) <= await getUserAccessLevel(id, chat_id):
        return await message.reply(disable_mentions=1, message=messages.ignore_higher())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if await (await c.execute('select * from ignore where chat_id=%s and uid=%s',
                                      (chat_id, id))).fetchone() is None:
                await c.execute('insert into ignore (chat_id, uid) values (%s, %s)', (chat_id, id))
                await conn.commit()
    await message.reply(disable_mentions=1, message=messages.ignore(
        id, await getUserName(id), await getUserNickname(uid, chat_id)))


@bl.chat_message(SearchCMD('unignore'))
async def unignore(message: Message):
    uid = message.from_id
    if not await getUserPremium(uid):
        return await message.reply(disable_mentions=1, message=messages.no_prem())
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.ignore_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    chat_id = message.peer_id - 2000000000
    name = await getUserName(id)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from ignore where chat_id=%s and uid=%s', (chat_id, id))).rowcount:
                return await message.reply(disable_mentions=1, message=messages.unignore_not_ignored())
            await conn.commit()
    await message.reply(disable_mentions=1, message=messages.unignore(id, name, await getUserNickname(uid, chat_id)))


@bl.chat_message(SearchCMD('ignorelist'))
async def ignorelist(message: Message):
    if int(await getUserPremium(message.from_id)) <= 0:
        return await message.reply(disable_mentions=1, message=messages.no_prem())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            ids = [i[0] for i in await (
                await c.execute('select uid from ignore where chat_id=%s', (message.peer_id - 2000000000,))).fetchall()]
    raw_names = await api.users.get(user_ids=ids)
    names = []
    for i in raw_names:
        names.append(f'{i.first_name} {i.last_name}')
    await message.reply(disable_mentions=1, message=messages.ignorelist(ids, names))


@bl.chat_message(SearchCMD('chatlimit'))
async def chatlimit(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if not await getUserPremium(uid):
        return await message.reply(disable_mentions=1, message=messages.no_prem())
    data = message.text.split()
    if len(data) != 2:
        return await message.reply(disable_mentions=1, message=messages.chatlimit_hint())

    t = data[1]
    pfx = t[-1]
    if t != '0':
        if not t[:-1].isdigit() or pfx not in ['s', 'm', 'h']:
            return await message.reply(disable_mentions=1, message=messages.chatlimit_hint())
        st = int(t[:-1])
        tst = int(st)
        if pfx == 'm':
            st *= 60
        elif pfx == 'h':
            st *= 60 * 60
    else:
        st = 0
        tst = 0

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chlim = await (await c.execute('select time from chatlimit where chat_id=%s', (chat_id,))).fetchone()
            lpos = chlim[0] if chlim else 1
            if chlim:
                await c.execute('update chatlimit set time = %s where chat_id=%s', (st, chat_id,))
            else:
                await c.execute('insert into chatlimit (chat_id, time) values (%s, %s)', (chat_id, st))
            await conn.commit()

    await message.reply(disable_mentions=1, message=messages.chatlimit(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), tst, pfx, lpos))


@bl.chat_message(SearchCMD('resetnick'))
async def resetnick(message: Message):
    await message.reply(disable_mentions=1, message=messages.resetnick_yon(),
                        keyboard=keyboard.resetnick_accept(message.from_id, message.peer_id - 2000000000))


@bl.chat_message(SearchCMD('resetaccess'))
async def resetaccess(message: Message):
    data = message.text.split()
    if len(data) != 2 or not data[1].isdigit() or int(data[1]) < 1 or int(data[1]) > 6:
        return await message.reply(disable_mentions=1, message=messages.resetaccess_hint())
    await message.reply(disable_mentions=1, message=messages.resetaccess_yon(data[1]),
                        keyboard=keyboard.resetaccess_accept(message.from_id, message.peer_id - 2000000000, data[1]))


@bl.chat_message(SearchCMD('notif'))
async def notif(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) >= 2:
        name = ' '.join(data[1:])
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                notif = (await (await c.execute('select count(*) as c from notifications where chat_id=%s and name=%s',
                                                (chat_id, name))).fetchone())[0]
                if not notif:
                    await c.execute(
                        "insert into notifications (chat_id, tag, every, status, time, name, description, text) "
                        "values (%s, 1, -1, 1, %s, %s, '', '')", (chat_id, int(time.time() - 5), name))
                    await conn.commit()
                    return await message.reply(disable_mentions=1, message=messages.notification(
                        name, '', time.time(), -1, 1, 1), keyboard=keyboard.notification(uid, 1, name))
        return await message.reply(disable_mentions=1, message=messages.notif_already_exist(name))
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            activenotifs = (await (await c.execute(
                'select count(*) as c from notifications where chat_id=%s and status=1', (chat_id,))).fetchone())[0]
            notifs = (await (await c.execute(
                'select count(*) as c from notifications where chat_id=%s', (chat_id,))).fetchone())[0]
    await message.reply(disable_mentions=1, message=messages.notif(notifs, activenotifs), keyboard=keyboard.notif(uid))


@bl.chat_message(SearchCMD('purge'))
async def purge(message: Message):
    chat_id = message.peer_id - 2000000000
    edit = await message.reply(disable_mentions=1, message=messages.purge_start())
    users = [i.member_id for i in (await api.messages.get_conversation_members(peer_id=message.peer_id)).items]
    dtdnicknames = 0
    dtdaccesslevels = 0
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            for i in await (await c.execute('select id, uid from nickname where chat_id=%s', (chat_id,))).fetchall():
                if i[1] not in users:
                    await c.execute('delete from nickname where id=%s', (i[0],))
                    dtdnicknames += 1
            for i in await (await c.execute('select id, uid from accesslvl where chat_id=%s', (chat_id,))).fetchall():
                if i[1] not in users:
                    x = await (await c.execute('delete from accesslvl where id=%s returning uid', (i[0],))).fetchone()
                    await setChatMute(x[0], chat_id, 0)
                    dtdaccesslevels += 1
            await conn.commit()
    await editMessage(messages.purge(dtdnicknames, dtdaccesslevels) if dtdnicknames > 0 or dtdaccesslevels > 0 else
                      messages.purge_empty(), message.peer_id, edit.conversation_message_id)
