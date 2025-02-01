import time
from ast import literal_eval
from datetime import datetime

from vkbottle import VKAPIError
from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserName, getUserNickname, isChatAdmin, \
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
        return await message.reply(disable_mentions=1, message=messages.kick_hint())
    if id == uid:
        return await message.reply(disable_mentions=1, message=messages.kick_myself())

    if await isChatAdmin(id, chat_id):
        return await message.reply(disable_mentions=1, message=messages.kick_access(
            id, await getUserName(id), await getUserNickname(id, chat_id)))

    uacc = await getUserAccessLevel(uid, chat_id)
    if await getUserAccessLevel(id, chat_id) >= uacc:
        return await message.reply(disable_mentions=1, message=messages.kick_higher())

    kick_cause = ' '.join(message.text.split()[1 + (not message.reply_message):])
    await message.reply(disable_mentions=1, message=messages.kick(
        await getUserName(uid), await getUserNickname(uid, chat_id), uid, await getUserName(id),
        await getUserNickname(id, chat_id), id, kick_cause if kick_cause else 'Причина не указана') if await kickUser(
        id, chat_id) else messages.kick_error())


@bl.chat_message(SearchCMD('mkick'))
async def mkick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if not await getUserPremium(uid):
        return await message.reply(disable_mentions=1, message=messages.no_prem())

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
        if id and int(id) != int(uid):
            ids.append(int(id))

    strids = [str(x) for x in ids if str(x).isdigit()]
    if len(strids) <= 0:
        return await message.reply(disable_mentions=1, message=messages.mkick_error())

    names = await API.users.get(user_ids=strids)
    u_acc = await getUserAccessLevel(uid, chat_id)
    kick_res_count = 0
    msg = ''
    for ind, id in enumerate(strids):
        if u_acc <= await getUserAccessLevel(id, chat_id) or not await kickUser(id, chat_id):
            continue
        ch_nickname = await getUserNickname(id, chat_id)
        msg += f'➖ [id{id}|{ch_nickname if ch_nickname else f"{names[ind].first_name} {names[ind].last_name}"}]\n'
        kick_res_count += 1
    if kick_res_count > 0:
        return await message.reply(
            disable_mentions=1, message=f'💬 Пользователь [id{uid}|{await getUserName(uid)}] исключил '
                                        f'следующих пользователей из данной беседы:\n' + msg)
    await message.reply(disable_mentions=1, message=messages.mkick_no_kick())


@bl.chat_message(SearchCMD('mute'))
async def mute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.mute_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if id == uid:
        return await message.reply(disable_mentions=1, message=messages.mute_myself())

    try:
        if (mute_time := int(data[1 + (not message.reply_message)])) < 1:
            raise Exception
    except:
        return await message.reply(disable_mentions=1, message=messages.mute_hint())

    if mute_time == id:
        return await message.reply(disable_mentions=1, message=messages.mute_hint())

    if await getUserAccessLevel(id, chat_id) >= await getUserAccessLevel(uid, chat_id):
        return await message.reply(disable_mentions=1, message=messages.mute_higher())

    if (ch_mute := await getUserMute(id, chat_id)) >= time.time():
        return await message.reply(disable_mentions=1, message=messages.already_muted(
            await getUserName(id), await getUserNickname(id, chat_id), id, ch_mute))

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

    mute_cause = ' '.join(data[2 + + (not message.reply_message):])
    if not mute_cause:
        mute_cause = 'Без указания причины'
    if not mute_date:
        mute_date = 'Дата неизвестна'

    mute_time *= 60
    mute_times.append(mute_time)
    mute_causes.append(mute_cause)
    u_name = await getUserName(uid)
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
    await message.reply(disable_mentions=1, message=messages.mute(
        u_name, await getUserNickname(uid, chat_id), uid, await getUserName(id), await getUserNickname(id, chat_id),
        id, mute_cause, mute_time // 60), keyboard=keyboard.punish_unpunish(
        uid, id, 'mute', message.conversation_message_id))


@bl.chat_message(SearchCMD('warn'))
async def warn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id or (len(data) < 2 and message.reply_message is None):
        return await message.reply(disable_mentions=1, message=messages.warn_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if id == uid:
        return await message.reply(disable_mentions=1, message=messages.warn_myself())
    if await getUserAccessLevel(id, chat_id) >= await getUserAccessLevel(uid, chat_id):
        return await message.reply(disable_mentions=1, message=messages.warn_higher())

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
    warn_cause = ' '.join(data[1 + (not message.reply_message):])
    if warn_cause is None or warn_cause == '':
        warn_cause = 'Без указания причины'
    warn_times.append(0)
    warn_causes.append(warn_cause)
    u_name = await getUserName(uid)
    warn_names.append(f'[id{uid}|{u_name}]')
    warn_dates.append(datetime.now().strftime('%Y.%m.%d %H:%M:%S'))

    if warns >= 3:
        warns = 0
        await kickUser(id, chat_id)
        msg = messages.warn_kick(u_name, await getUserNickname(uid, chat_id), uid, await getUserName(id),
                                 await getUserNickname(id, chat_id), id, warn_cause)
    else:
        msg = messages.warn(u_name, await getUserNickname(uid, chat_id), uid, await getUserName(id),
                            await getUserNickname(id, chat_id), id, warn_cause)

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
    await message.reply(disable_mentions=1, message=msg, keyboard=keyboard.punish_unpunish(
        uid, id, 'warn', message.conversation_message_id))


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
        return await message.reply(disable_mentions=1, message=messages.clear_hint())
    names = {}
    for i in u_ids:
        names[i] = await getUserName(int(i))

    for ind, i in enumerate(u_ids):
        if int(i) < 0:
            continue
        if await getUserAccessLevel(uid, chat_id) < await getUserAccessLevel(i, chat_id):
            cmids.pop(ind)

    if len(cmids) > 0:
        try:
            await API.messages.delete(peer_id=2000000000 + chat_id, cmids=cmids, delete_for_all=True)
            await message.reply(disable_mentions=1, message=messages.clear(names, await getUserName(uid), uid))
        except VKAPIError[15]:
            await message.reply(disable_mentions=1, message=messages.clear_admin())
        except VKAPIError:
            await message.reply(disable_mentions=1, message=messages.clear_old())
    else:
        await message.reply(disable_mentions=1, message=messages.clear_higher())


@bl.chat_message(SearchCMD('snick'))
async def snick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id or len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.snick_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())

    nickname = ' '.join(data[1 + (not message.reply_message):])
    if len(nickname) <= 0:
        return await message.reply(disable_mentions=1, message=messages.snick_hint())
    if len(nickname) >= 46 or '[' in nickname or ']' in nickname:
        return await message.reply(disable_mentions=1, message=messages.snick_too_long_nickname())

    if await getUserAccessLevel(id, chat_id) > await getUserAccessLevel(uid, chat_id):
        return await message.reply(disable_mentions=1, message=messages.snick_higher())

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update nickname set nickname = %s where chat_id=%s and uid=%s',
                                    (nickname, chat_id, id))).rowcount:
                await c.execute(
                    'insert into nickname (uid, chat_id, nickname) VALUES (%s, %s, %s)', (id, chat_id, nickname))
            await conn.commit()

    await message.reply(disable_mentions=1, message=messages.snick(
        uid, await getUserName(id), await getUserNickname(uid, chat_id), id, await getUserName(id),
        await getUserNickname(id, chat_id), nickname))


@bl.chat_message(SearchCMD('rnick'))
async def rnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.snick_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())

    if await getUserAccessLevel(id, chat_id) > await getUserAccessLevel(uid, chat_id):
        return await message.reply(disable_mentions=1, message=messages.rnick_higher())
    if not (ch_nickname := await getUserNickname(id, chat_id)):
        return await message.reply(disable_mentions=1, message=messages.rnick_user_has_no_nick())

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from nickname where chat_id=%s and uid=%s', (chat_id, id))
            await conn.commit()
    await message.reply(disable_mentions=1, message=messages.rnick(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), id, await getUserName(id), ch_nickname))


@bl.chat_message(SearchCMD('nlist'))
async def nlist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, nickname from nickname where chat_id=%s and uid>0 and uid=ANY(%s) and nickname is not null'
                ' order by nickname', (
                    message.peer_id - 2000000000, [i.member_id for i in (await API.messages.get_conversation_members(
                        peer_id=message.peer_id)).items]))).fetchall()
    count = len(res)
    res = res[:30]
    await message.reply(disable_mentions=1, message=messages.nlist(
        res, await API.users.get(user_ids=[i[0] for i in res])), keyboard=keyboard.nlist(message.from_id, 0, count))


@bl.chat_message(SearchCMD('getnick'))
async def getnick(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.getnick_hint())
    query = ' '.join(data[1:])
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                "select uid, nickname from nickname where chat_id=%s and uid>0 and nickname like %s order by nickname "
                "limit 30", (chat_id, '%%' + query + '%%'))).fetchall()
    if len(res) > 0:
        await message.reply(disable_mentions=1, message=await messages.getnick(res, query))
    else:
        await message.reply(disable_mentions=1, message=messages.getnick_no_result(query))


@bl.chat_message(SearchCMD('staff'))
async def staff(message: Message):
    chat_id = message.peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, access_level from accesslvl where chat_id=%s and uid>0 and access_level>0 and '
                'access_level<8 order by access_level desc', (chat_id,))).fetchall()
    await message.reply(disable_mentions=1, message=await messages.staff(
        res, await API.users.get(user_ids=[i[0] for i in res if i[0] > 0]), chat_id))


@bl.chat_message(SearchCMD('olist'))
async def olist(message: Message):
    members = await API.users.get(user_ids=[f'{i.member_id}' for i in (
        await API.messages.get_conversation_members(peer_id=message.peer_id - 2000000000 + 2000000000)).items],
                                  fields='online')
    members_online = {}
    for i in members:
        if i.online:
            if i.online_mobile or i.online_app:
                online_mobile = True
            else:
                online_mobile = False
            members_online[f'[id{i.id}|{i.first_name} {i.last_name}]'] = online_mobile
    await message.reply(disable_mentions=1, message=messages.olist(members_online))


@bl.chat_message(SearchCMD('check'))
async def check(message: Message):
    chat_id = message.peer_id - 2000000000
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.check_help())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())

    ban = await getUserBan(id, chat_id) - time.time()
    mute = await getUserMute(id, chat_id) - time.time()
    msg = messages.check(id, await getUserName(id), await getUserNickname(id, chat_id),
                         ban if ban > 0 else 0, await getUserWarns(id, chat_id), mute if mute > 0 else 0)
    kb = keyboard.check(message.from_id, id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)
