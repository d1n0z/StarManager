import time

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserName, getUserNickname, getUserAccessLevel, getUserPremium, editMessage, \
    getgpool, getpool
from config.config import API
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('gdelaccess'))
async def gdelaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.gdelaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.delaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getgpool(chat_id)):
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(id)
    u_name = await getUserName(uid)
    ch_nickname = await getUserNickname(id, chat_id)
    u_nickname = await getUserNickname(uid, chat_id)

    msg = messages.gdelaccess_start(uid, u_name, u_nickname, id, name, ch_nickname, len(chats))
    edit = await message.reply(disable_mentions=1, message=msg)

    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('gdelaccess', chat_id, u_acc) or await getUserAccessLevel(id, chat_id) > u_acc:
            continue
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if (await c.execute('delete from accesslvl where chat_id=%s and uid=%s', (chat_id, id))).rowcount:
                    success += 1
                    await conn.commit()

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.gdelaccess(id, name, nick, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gsetaccess'))
async def gsetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 2 and message.reply_message is None) or
            (len(data) <= 1 and message.reply_message is not None)):
        msg = messages.gsetaccess_hint()
        await message.reply(message=msg, disable_mentions=1)
        return
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.gsetaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.setaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        acc = int(data[-1])
        if acc <= 0 or acc >= 7:
            raise
    except:
        msg = messages.setacc_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getgpool(chat_id)):
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    u_name = await getUserName(uid)
    name = await getUserName(id)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)

    msg = messages.gsetaccess_start(uid, u_name, u_nickname, id, name, ch_nickname, len(chats))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)

        if acc >= u_acc or ch_acc >= u_acc or ch_acc >= acc or not await haveAccess('gsetaccess', chat_id, u_acc):
            continue

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute('update accesslvl set access_level = %s where chat_id=%s and uid=%s',
                                        (acc, chat_id, id))).rowcount:
                    await c.execute(
                        'insert into accesslvl (uid, chat_id, access_level) values (%s, %s, %s)', (id, chat_id, acc))
                await conn.commit()
        success += 1

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.gsetaccess(id, name, nick, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('demote'))
async def demote(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    msg = messages.demote_choose()
    kb = keyboard.demote_choose(uid, chat_id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('ssetaccess'))
async def ssetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 3 and message.reply_message is None) or
            (len(data) <= 2 and message.reply_message is not None)):
        msg = messages.ssetaccess_hint()
        await message.reply(message=msg, disable_mentions=1)
        return
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if not id:
        msg = messages.ssetaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.setaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        acc = int(data[-1])
        if acc <= 0 or acc >= 7:
            raise
    except:
        msg = messages.setacc_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getpool(chat_id, data[1])):
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    u_name = await getUserName(uid)
    name = await getUserName(id)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)

    msg = messages.ssetaccess_start(uid, u_name, u_nickname, id, name, ch_nickname, len(chats), data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if acc >= u_acc or ch_acc >= u_acc or ch_acc >= acc or not await haveAccess('ssetaccess', chat_id, u_acc):
            continue

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute('update accesslvl set access_level = %s where chat_id=%s and uid=%s',
                                        (acc, chat_id, id))).rowcount:
                    await c.execute(
                        'insert into accesslvl (uid, chat_id, access_level) values (%s, %s, %s)', (id, chat_id, acc))
                await conn.commit()
        success += 1

    ch_nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.ssetaccess(id, name, ch_nick, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('sdelaccess'))
async def sdelaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 2 and message.reply_message is None) or
            (len(data) <= 1 and message.reply_message is not None)):
        msg = messages.sdelaccess_hint()
        await message.reply(message=msg, disable_mentions=1)
        return
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if not id:
        msg = messages.sdelaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.delaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getpool(chat_id, data[1])):
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(id)
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)

    msg = messages.sdelaccess_start(uid, u_name, u_nickname, id, name, ch_nickname, data[1], len(chats))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('sdelaccess', chat_id, u_acc) or await getUserAccessLevel(id, chat_id) > u_acc:
            continue

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if (await c.execute('delete from accesslvl where chat_id=%s and uid=%s', (chat_id, id))).rowcount:
                    success += 1
                    await conn.commit()

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.sdelaccess(id, name, nick, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('ignore'))
async def ignore(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.ignore_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if await getUserAccessLevel(uid, chat_id) <= await getUserAccessLevel(id, chat_id):
        msg = messages.ignore_higher()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(id)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if await (await c.execute('select * from ignore where chat_id=%s and uid=%s',
                                      (chat_id, id))).fetchone() is None:
                await c.execute('insert into ignore (chat_id, uid) values (%s, %s)', (chat_id, id))
                await conn.commit()

    nick = await getUserNickname(uid, chat_id)
    msg = messages.ignore(id, name, nick)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('unignore'))
async def unignore(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.ignore_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(id)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from ignore where chat_id=%s and uid=%s', (chat_id, id))).rowcount:
                msg = messages.unignore_not_ignored()
                await message.reply(disable_mentions=1, message=msg)
                return
            await conn.commit()

    nick = await getUserNickname(uid, chat_id)
    msg = messages.unignore(id, name, nick)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('ignorelist'))
async def ignorelist(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if int(u_prem) <= 0:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            ids = [i[0] for i in await (
                await c.execute('select uid from ignore where chat_id=%s', (chat_id,))).fetchall()]
    raw_names = await API.users.get(user_ids=','.join(ids))
    names = []
    for i in raw_names:
        names.append(f'{i.first_name} {i.last_name}')

    msg = messages.ignorelist(ids, names)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('chatlimit'))
async def chatlimit(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    if len(data) != 2:
        msg = messages.chatlimit_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    t = data[1]
    pfx = t[-1]
    if t != '0':
        if not t[:-1].isdigit() or pfx not in ['s', 'm', 'h']:
            msg = messages.chatlimit_hint()
            await message.reply(disable_mentions=1, message=msg)
            return

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
                await c.execute('update chatlimit set time = %s where chat_id=%s', (st,))
            else:
                await c.execute('insert into chatlimit (chat_id, time) values (%s, %s)', (chat_id, st))
            await conn.commit()

    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)
    msg = messages.chatlimit(uid, name, nick, tst, pfx, lpos)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('resetnick'))
async def resetnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    kb = keyboard.resetnick_accept(uid, chat_id)
    msg = messages.resetnick_yon()
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('resetaccess'))
async def resetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) != 2 or not data[1].isdigit() or int(data[1]) < 1 or int(data[1]) > 6:
        msg = messages.resetaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    uid = message.from_id
    kb = keyboard.resetaccess_accept(uid, chat_id, data[1])
    msg = messages.resetaccess_yon(data[1])
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


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
                    msg = messages.notification(name, '', time.time(), -1, 1, 1)
                    kb = keyboard.notification(uid, 1, name)
                    await message.reply(disable_mentions=1, message=msg, keyboard=kb)
                    return
        msg = messages.notif_already_exist(notif.name)
        await message.reply(disable_mentions=1, message=msg)
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            activenotifs = (await (await c.execute(
                'select count(*) as c from notifications where chat_id=%s and status=1', (chat_id,))).fetchone())[0]
            notifs = (await (await c.execute(
                'select count(*) as c from notifications where chat_id=%s', (chat_id,))).fetchone())[0]
    msg = messages.notif(notifs, activenotifs)
    kb = keyboard.notif(uid)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('purge'))
async def purge(message: Message):
    chat_id = message.peer_id - 2000000000

    users = [i.member_id for i in (await API.messages.get_conversation_members(peer_id=message.peer_id)).items]
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
                    await c.execute('delete from accesslvl where id=%s', (i[0],))
                    dtdaccesslevels += 1
            await conn.commit()

    msg = messages.purge_start()
    edit = await message.reply(disable_mentions=1, message=msg)
    if dtdnicknames > 0 or dtdaccesslevels > 0:
        msg = messages.purge(dtdnicknames, dtdaccesslevels)
    else:
        msg = messages.purge_empty()
    await editMessage(msg, message.peer_id, edit.conversation_message_id)
