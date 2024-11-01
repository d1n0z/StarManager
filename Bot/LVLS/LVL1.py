import time
from ast import literal_eval
from datetime import datetime

from vkbottle import VKAPIError
from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserName, getUserNickname, getGroupName, isChatAdmin, \
    getUserAccessLevel, kickUser, getUserPremium, getUserMute, setChatMute, getUserBan, getUserWarns
from config.config import API
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('kick'))
async def kick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        msg = messages.kick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id == uid:
        msg = messages.kick_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    if id > 0:
        kicking_acc = await getUserAccessLevel(id, chat_id)
        kicking_name = await getUserName(id)
        kicking_nick = await getUserNickname(id, chat_id)
    else:
        kicking_acc = 0
        kicking_name = await getGroupName(id)
        kicking_nick = None

    if await isChatAdmin(id, chat_id):
        msg = messages.kick_access(id, kicking_name, kicking_nick)
        await message.reply(disable_mentions=1, message=msg)
        return

    uacc = await getUserAccessLevel(uid, chat_id)
    if kicking_acc >= uacc:
        msg = messages.kick_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    if message.reply_message is None:
        msg = message.text.lower()[message.text.lower().find(' ') + 1:]
    else:
        msg = message.text.lower()
    kick_cause = msg.find(' ')
    if kick_cause == -1:
        kick_cause = 'Причина не указана'
    else:
        kick_cause = msg[kick_cause + 1:]

    kicker_name = await getUserName(uid)
    kicker_nick = await getUserNickname(uid, chat_id)

    msg = messages.kick(kicker_name, kicker_nick, uid, kicking_name, kicking_nick, id, kick_cause)

    if await kickUser(id, chat_id) == 0:
        msg = messages.kick_error()

    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('mkick'))
async def mkick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not bool(u_prem):
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    ids = []
    for i in data[1:]:
        id = None
        if i.find('[id') != -1:
            id = i[i.find('[id') + 3:i.find('|')]
        elif i.find('vk.') != -1:
            id = i[i.find('vk.'):]
            id = id[id.find('/') + 1:]
            id = await API.users.get(user_ids=id)
            id = id[0].id
        elif i.isdigit():
            id = i
        if id is not None and int(id) != int(uid):
            ids.append(int(id))

    strids = [str(x) for x in ids if str(x).isdigit()]
    if len(strids) <= 0:
        msg = messages.mkick_error()
        await message.reply(disable_mentions=1, message=msg)
        return
    names = await API.users.get(user_ids=strids)
    uname = await getUserName(uid)
    u_acc = await getUserAccessLevel(uid, chat_id)
    msg = f'💬 Пользователь [id{uid}|{uname}] исключил ' \
          f'следующих пользователей из данной беседы:\n'
    kick_res_count = 0
    for ind, id in enumerate(strids):
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc > ch_acc:
            ch_nickname = await getUserNickname(id, chat_id)
            if ch_nickname is not None and len(ch_nickname) > 0:
                name = ch_nickname
            else:
                name = f'{names[ind].first_name} {names[ind].last_name}'
            kick_res = await kickUser(id, chat_id)
            kick_res_count += int(kick_res)
            if kick_res == 1:
                msg += f'➖ [id{id}|{name}]\n'
    if kick_res_count > 0:
        await message.reply(disable_mentions=1, message=msg)
        return
    msg = messages.mkick_no_kick()
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('mute'))
async def mute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.mute_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id == uid:
        msg = messages.mute_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    user = await API.users.get(user_ids=id)
    if user[0].deactivated:
        msg = messages.id_deleted()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        if message.reply_message is None:
            mute_time = int(data[2])
        else:
            mute_time = int(data[1])
        if mute_time < 1:
            raise Exception
    except:
        msg = messages.mute_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if mute_time == id:
        msg = messages.mute_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    mute_time *= 60

    if message.reply_message is None:
        mute_cause = ' '.join(data[3:])
    else:
        mute_cause = ' '.join(data[2:])

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)

    if ch_acc >= u_acc:
        msg = messages.mute_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_mute = await getUserMute(id, chat_id)
    ch_name = await getUserName(id)
    ch_nick = await getUserNickname(id, chat_id)
    u_name = await getUserName(uid)
    u_nick = await getUserNickname(uid, chat_id)

    if ch_mute >= time.time():
        msg = messages.already_muted(ch_name, ch_nick, id, ch_mute)
        await message.reply(disable_mentions=1, message=msg)
        return

    msg = messages.mute(u_name, u_nick, uid, ch_name, ch_nick, id, mute_cause, int(mute_time / 60))
    mute_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            ms = await (await c.execute(
                'select last_mutes_times, last_mutes_causes, last_mutes_names, last_mutes_dates from mute where '
                'chat_id=%s and uid=%s', (chat_id, id))).fetchone()
    if ms is not None:
        mute_times = literal_eval(ms[0])
        mute_causes = literal_eval(ms[1])
        mute_names = literal_eval(ms[2])
        mute_dates = literal_eval(ms[3])
    else:
        mute_times, mute_causes, mute_names, mute_dates = [], [], [], []

    if mute_cause is None:
        mute_cause = 'Без указания причины'
    if mute_date is None:
        mute_date = 'Дата неизвестна'

    mute_times.append(mute_time)
    mute_causes.append(mute_cause)
    mute_names.append(f'[id{uid}|{u_name}]')
    mute_dates.append(mute_date)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute(
                    'update mute set mute = %s, last_mutes_times = %s, last_mutes_causes = %s, last_mutes_names = %s, '
                    'last_mutes_dates = %s where chat_id=%s and uid=%s',
                    (int(time.time() + mute_time), f"{mute_times}", f"{mute_causes}", f"{mute_names}", f"{mute_dates}",
                     chat_id, id))).rowcount:
                await c.execute(
                    'insert into mute (uid, chat_id, mute, last_mutes_times, last_mutes_causes, last_mutes_names, '
                    'last_mutes_dates) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (id, chat_id, int(time.time() + mute_time), f"{mute_times}", f"{mute_causes}", f"{mute_names}",
                     f"{mute_dates}"))
            await conn.commit()

    await setChatMute(id, chat_id, mute_time)

    kb = keyboard.punish_unpunish(uid, id, 'mute', message.conversation_message_id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('warn'))
async def warn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.warn_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id == uid:
        msg = messages.warn_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    if len(data) < 2 and message.reply_message is None:
        msg = messages.warn_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if message.reply_message is None:
        warn_cause = ' '.join(data[2:])
    else:
        warn_cause = ' '.join(data[1:])

    warning_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    u_nickname = await getUserNickname(uid, chat_id)
    u_name = await getUserName(uid)

    if warning_acc >= u_acc:
        msg = messages.warn_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_name = await getUserName(id)
    ch_nick = await getUserNickname(id, chat_id)
    warn_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute('select warns, last_warns_times, last_warns_causes, last_warns_names, '
                                         'last_warns_dates from warn where chat_id=%s and uid=%s',
                                         (chat_id, id))).fetchone()
    if res is not None:
        warns = res[0] + 1
        warn_times = literal_eval(res[1])
        warn_causes = literal_eval(res[2])
        warn_names = literal_eval(res[3])
        warn_dates = literal_eval(res[4])
    else:
        warns = 1
        warn_times, warn_causes, warn_names, warn_dates = [], [], [], []
    if warn_cause is None or warn_cause == '':
        warn_cause = 'Без указания причины'
    warn_times.append(0)
    warn_causes.append(warn_cause)
    warn_names.append(f'[id{uid}|{u_name}]')
    warn_dates.append(warn_date)

    if warns >= 3:
        warns = 0
        await kickUser(id, chat_id)
        msg = messages.warn_kick(u_name, u_nickname, uid, ch_name, ch_nick, id, warn_cause)
    else:
        msg = messages.warn(u_name, u_nickname, uid, ch_name, ch_nick, id, warn_cause)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute(
                    'update warn set warns = %s, last_warns_times = %s, last_warns_causes = %s, last_warns_names = %s, '
                    'last_warns_dates = %s where chat_id=%s and uid=%s',
                    (warns, f"{warn_times}", f"{warn_causes}", f"{warn_names}", f"{warn_dates}", chat_id,
                     id))).rowcount:
                await c.execute(
                    'insert into warn (uid, chat_id, warns, last_warns_times, last_warns_causes, last_warns_names, '
                    'last_warns_dates) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (id, chat_id, warns, f"{warn_times}", f"{warn_causes}", f"{warn_names}", f"{warn_dates}"))
            await conn.commit()

    kb = keyboard.punish_unpunish(uid, id, 'warn', message.conversation_message_id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('clear'))
async def clear(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_ids = []
    cmids = []
    if len(message.fwd_messages) > 0:
        for i in message.fwd_messages:
            u_ids.append(str(i.from_id))
            cmids.append(str(i.conversation_message_id))
    if message.reply_message is not None:
        u_ids.append(str(message.reply_message.from_id))
        cmids.append(str(message.reply_message.conversation_message_id))
    if len(u_ids) <= 0:
        msg = messages.clear_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    name = await API.users.get(user_ids=u_ids)
    u_name = await getUserName(uid)
    names = []
    for i in name:
        names.append(f"{i.first_name} {i.last_name}")

    for ind, i in enumerate(u_ids):
        if int(i) < 0:
            continue
        if await getUserAccessLevel(uid, chat_id) < await getUserAccessLevel(i, chat_id):
            u_ids.pop(ind)
            cmids.pop(ind)

    if len(cmids) > 0:
        try:
            await API.messages.delete(peer_id=2000000000 + chat_id, cmids=cmids, delete_for_all=True)
            msg = messages.clear(names, u_ids, u_name, uid)
            await message.reply(disable_mentions=1, message=msg)
        except VKAPIError[15]:
            msg = messages.clear_admin()
            await message.reply(disable_mentions=1, message=msg)
        except VKAPIError:
            msg = messages.clear_old()
            await message.reply(disable_mentions=1, message=msg)
    else:
        msg = messages.clear_higher()
        await message.reply(disable_mentions=1, message=msg)

    for i in u_ids:
        if int(i) < 0:
            msg = messages.clear_hint()
            await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('snick'))
async def snick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.snick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    nickname = data[2:] if message.reply_message is None else data[1:]
    if len(nickname) <= 0:
        msg = messages.snick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    nickname = ' '.join(nickname)
    if len(nickname) >= 46 or ('[' in nickname or ']' in nickname):
        msg = messages.snick_too_long_nickname()
        await message.reply(disable_mentions=1, message=msg)
        return
    if len(data) <= 1:
        msg = messages.snick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc > u_acc:
        msg = messages.snick_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update nickname set nickname = %s where chat_id=%s and chat_id=%s',
                                    (nickname, chat_id, id))).rowcount:
                await c.execute(
                    'insert into nickname (uid, chat_id, nickname) VALUES (%s, %s, %s)', (id, chat_id, nickname))
            await conn.commit()

    u_name = await getUserName(uid)
    name = await getUserName(id)
    msg = messages.snick(uid, u_name, u_nickname, id, name, ch_nickname, nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('rnick'))
async def rnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.snick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc > u_acc:
        msg = messages.rnick_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_nickname = await getUserNickname(id, chat_id)
    if ch_nickname is None:
        msg = messages.rnick_user_has_no_nick()
        await message.reply(disable_mentions=1, message=msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from nickname where chat_id=%s and uid=%s', (chat_id, id))
            await conn.commit()
    u_name = await getUserName(uid)
    name = await getUserName(id)
    u_nick = await getUserNickname(uid, chat_id)
    msg = messages.rnick(uid, u_name, u_nick, id, name, ch_nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('nlist'))
async def nlist(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    members_uid = [i.member_id for i in members]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, nickname from nickname where chat_id=%s and uid>0 and uid=ANY(%s) and nickname is not null'
                ' order by nickname', (chat_id, members_uid))).fetchall()
    count = len(res)
    res = res[:30]
    names = await API.users.get(user_ids=[i[0] for i in res])
    msg = messages.nlist(res, names)
    kb = keyboard.nlist(uid, 0, count)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('getnick'))
async def getnick(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.getnick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    query = ' '.join(data[1:])
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                "select uid, nickname from nickname where chat_id=%s and uid>0 and nickname like %s order by nickname "
                "limit 30", (chat_id, '%%' + query + '%%'))).fetchall()
    lres = len(res)
    names = await API.users.get(user_ids=[i[0] for i in res])
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    if lres > 0:
        msg = messages.getnick(res, names, members, query)
    else:
        msg = messages.getnick_no_result(query)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('staff'))
async def staff(message: Message):
    chat_id = message.peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, access_level from accesslvl where chat_id=%s and uid>0 and access_level>0 order by '
                'access_level desc', (chat_id,))).fetchall()
    names = await API.users.get(user_ids=[i[0] for i in res])
    msg = await messages.staff(res, names, chat_id)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('olist'))
async def olist(message: Message):
    chat_id = message.peer_id - 2000000000
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    members = [f'{i.member_id}' for i in members]
    members = await API.users.get(user_ids=members, fields='online')
    members_online = {}
    for i in members:
        if i.online:
            if i.online_mobile or i.online_app:
                online_mobile = True
            else:
                online_mobile = False
            members_online[f'[id{i.id}|{i.first_name} {i.last_name}]'] = online_mobile

    msg = messages.olist(members_online)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('check'))
async def check(message: Message):
    chat_id = message.peer_id - 2000000000
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.check_help()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    ban = await getUserBan(id, chat_id) - time.time()
    if ban < 0:
        ban = 0
    mute = await getUserMute(id, chat_id) - time.time()
    if mute < 0:
        mute = 0
    warn = await getUserWarns(id, chat_id)

    name = await getUserName(id)
    nickname = await getUserNickname(id, chat_id)
    msg = messages.check(id, name, nickname, ban, warn, mute)
    kb = keyboard.check(message.from_id, id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)
