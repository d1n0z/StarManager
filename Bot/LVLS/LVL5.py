import time
from ast import literal_eval
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserAccessLevel, getUserName, getUserNickname, kickUser, \
    getUserBan, getChatName, getGroupName, getpool, sendMessage
from config.config import API
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('skick'))
async def skick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if not id:
        msg = messages.skick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.kick_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        kick_cause = ' '.join(data[3:])
        if kick_cause == str(id) or len(kick_cause) == 0:
            kick_cause = 'Причина не указана'
    except:
        kick_cause = 'Причина не указана'

    if not (chats := await getpool(chat_id, data[1])):
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)
    u_name = await getUserName(uid)
    ch_name = await getUserName(id)
    msg = messages.skick_start(uid, u_name, u_nickname, id, ch_name, ch_nickname, len(chats), data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('skick', chat_id, u_acc):
            continue

        kick_res = await kickUser(id, chat_id)
        ch_nickname = await getUserNickname(id, chat_id)
        u_nickname = await getUserNickname(uid, chat_id)

        if kick_res:
            msg = messages.kick(u_name, u_nickname, uid, ch_name, ch_nickname, id, kick_cause)
            await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
            success += 1

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.skick(id, ch_name, nick, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('sban'))
async def sban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if not id:
        msg = messages.sban_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.ban_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getpool(chat_id, data[1])):
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    u_name = await getUserName(uid)
    ch_name = await getUserName(id)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)

    if message.reply_message is None:
        cdata = data[3:]
    else:
        cdata = data[2:]

    if len(cdata) >= 1:
        if cdata[0].isdigit():
            ban_time = abs(int(cdata[0])) * 86400
            ban_cause = ' '.join(cdata[1:]) if len(cdata) > 1 else None
        else:
            ban_time = 86400 * 365
            ban_cause = ' '.join(cdata[0:])
    else:
        ban_time = 86400 * 365
        ban_cause = None

    msg = messages.sban_start(uid, u_name, u_nickname, id, ch_name, ch_nickname, len(chats), data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('sban', chat_id, u_acc):
            continue

        if await getUserBan(id, chat_id) >= time.time():
            continue
        u_nickname = await getUserNickname(uid, chat_id)
        ch_nickname = await getUserNickname(id, chat_id)
        msg = messages.ban(uid, u_name, u_nickname, id, ch_name, ch_nickname, ban_cause, ban_time // 86400)

        ban_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                res = await (await c.execute(
                    'select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates from ban where '
                    'chat_id=%s and uid=%s', (chat_id, id))).fetchone()
        if res is not None:
            ban_times = literal_eval(res[0])
            ban_causes = literal_eval(res[1])
            ban_names = literal_eval(res[2])
            ban_dates = literal_eval(res[3])
        else:
            ban_times, ban_causes, ban_names, ban_dates = [], [], [], []
        if ban_cause is None:
            ban_cause = 'Без указания причины'
        if ban_date is None:
            ban_date = 'Дата неизвестна'
        ban_times.append(ban_time)
        ban_causes.append(ban_cause)
        ban_names.append(f'[id{uid}|{u_name}]')
        ban_dates.append(ban_date)

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute(
                        'update ban set ban = %s, last_bans_times = %s, last_bans_causes = %s, last_bans_names = %s, '
                        'last_bans_dates = %s where chat_id=%s and uid=%s',
                        (int(time.time() + ban_time), f"{ban_times}", f"{ban_causes}", f"{ban_names}", f"{ban_dates}",
                            chat_id, id))).rowcount:
                    await c.execute(
                        'insert into ban (uid, chat_id, ban, last_bans_times, last_bans_causes, last_bans_names, '
                        'last_bans_dates) values (%s, %s, %s, %s, %s, %s, %s)',
                        (id, chat_id, int(time.time() + ban_time), f"{ban_times}", f"{ban_causes}", f"{ban_names}",
                         f"{ban_dates}"))
                await conn.commit()

        kick_res = await kickUser(id, chat_id)

        if kick_res:
            await API.messages.send(disable_mentions=1, random_id=0,
                                    message=msg, chat_id=chat_id)
        success += 1

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.sban(id, ch_name, nick, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('sunban'))
async def sunban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if not id:
        msg = messages.sunban_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.unban_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getpool(chat_id, data[1])):
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    u_name = await getUserName(uid)
    u_nick = await getUserNickname(uid, chat_id)
    ch_name = await getUserName(id)
    ch_nick = await getUserNickname(id, chat_id)
    msg = messages.sunban_start(uid, u_name, u_nick, id, ch_name, ch_nick, len(chats), data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if (u_acc < await haveAccess('sunban', chat_id, u_acc) or
                await getUserAccessLevel(id, chat_id) >= u_acc or
                await getUserBan(id, chat_id) <= time.time()):
            continue
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('update ban set ban = 0 where chat_id=%s and uid=%s', (chat_id, id))
                await conn.commit()
        success += 1

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    name = await getUserName(id)
    msg = messages.sunban(id, name, nick, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('ssnick'))
async def ssnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if not id or ((len(data) < 4 and message.reply_message is None) or
                  (len(data) < 3 and message.reply_message is not None)):
        msg = messages.ssnick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getpool(chat_id, data[1])):
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    nickname = ' '.join(data[3:]) if message.reply_message is None else ' '.join(data[2:])
    if not (46 >= len(nickname) and ('[' not in nickname and ']' not in nickname)):
        msg = messages.ssnick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    u_name = await getUserName(uid)
    name = await getUserName(id)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)
    msg = messages.ssnick_start(uid, u_name, u_nickname, id, name, ch_nickname, len(chats), data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('ssnick', chat_id, u_acc) or await getUserAccessLevel(id, chat_id) > u_acc:
            continue
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                ch_nick = await (await c.execute(
                    'select nickname from nickname where chat_id=%s and uid=%s', (chat_id, id))).fetchone()
                u_nick = await (await c.execute(
                    'select nickname from nickname where chat_id=%s and uid=%s', (chat_id, uid))).fetchone()
                if not (await c.execute('update nickname set nickname = %s where chat_id=%s and uid=%s',
                                        (nickname, chat_id, id))).rowcount:
                    await c.execute(
                        'insert into nickname (uid, chat_id, nickname) values (%s, %s, %s)', (id, chat_id, nickname))
                await conn.commit()
        msg = messages.snick(uid, u_name, u_nick[0] if u_nick else None, id, name,
                             ch_nick[0] if ch_nick else None, nickname)
        await sendMessage(chat_id + 2000000000, msg)
        success += 1

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.ssnick(id, name, nick, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('srnick'))
async def srnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if not id:
        msg = messages.srnick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getpool(chat_id, data[1])):
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_name = await getUserName(id)
    u_name = await getUserName(uid)
    ch_nickname = await getUserName(id)
    u_nickname = await getUserName(uid)
    msg = messages.srnick_start(uid, u_name, u_nickname, id, ch_name, ch_nickname, len(chats), data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('srnick', chat_id, u_acc):
            continue
        ch_acc = await getUserAccessLevel(id, chat_id)
        if ch_acc > u_acc:
            continue
        ch_nickname = await getUserName(id)
        u_nickname = await getUserName(uid)
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('delete from nickname where chat_id=%s and uid=%s', (chat_id, id))
                await conn.commit()
        try:
            msg = messages.rnick(uid, u_name, u_nickname, id, ch_name, ch_nickname)
            await API.messages.send(disable_mentions=1, random_id=0, message=msg,
                                    chat_id=chat_id)
        except:
            pass
        success += 1

    msg = messages.srnick(id, ch_name, len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('szov'))
async def szov(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) < 3:
        msg = messages.szov_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if not (chats := await getpool(chat_id, data[1])):
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(uid)
    nickname = await getUserNickname(uid, chat_id)
    msg = messages.szov_start(uid, name, nickname, len(chats), data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    text = ' '.join(data[2:])
    for chat_id in chats:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('szov', chat_id, u_acc):
            continue
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        nickname = await getUserNickname(uid, chat_id)
        msg = messages.zov(uid, name, nickname, text, members)
        await API.messages.send(random_id=0, message=msg, chat_id=chat_id)
        success += 1

    nick = await getUserNickname(uid, edit.peer_id - 2000000000)
    msg = messages.szov(uid, name, nick, data[1], len(chats), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('chat'))
async def chat(message: Message):
    chat_id = message.peer_id - 2000000000
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    id = [i for i in members if i.is_admin and i.is_owner][0].member_id

    names = await API.users.get(user_ids=id)
    try:
        name = f"{names[0].first_name} {names[0].last_name}"
        prefix = 'id'
    except:
        prefix = 'club'
        name = await getGroupName(-int(id))

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chatgroup = 'Привязана' if (await (await c.execute(
                'select count(*) as c from chatgroups where chat_id=%s', (chat_id,))).fetchone())[0] else 'Не привязана'
            gpool = 'Привязана' if (await (await c.execute(
                'select count(*) as c from gpool where chat_id=%s', (chat_id,))).fetchone())[0] else 'Не привязана'

            muted = (await (await c.execute('select count(*) as c from mute where chat_id=%s and mute>%s',
                                            (chat_id, int(time.time())))).fetchone())[0]
            banned = (await (await c.execute('select count(*) as c from ban where chat_id=%s and ban>%s',
                                             (chat_id, int(time.time())))).fetchone())[0]

            if bjd := await (await c.execute('select time from botjoineddate where chat_id=%s', (chat_id,))).fetchone():
                bjd = datetime.utcfromtimestamp(bjd[0]).strftime('%d.%m.%Y %H:%M')
            else:
                bjd = 'Невозможно определить'

    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    title = await getChatName(chat_id)

    if prefix == 'club':
        id = -int(id)
    msg = messages.chat(id, name, chat_id, chatgroup, gpool, muted, banned, len(members), bjd, prefix, title)
    kb = None if await getUserAccessLevel(message.from_id, chat_id) < 7 else keyboard.settings_goto(message.from_id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)
