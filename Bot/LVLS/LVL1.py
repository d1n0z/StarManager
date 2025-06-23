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
    getUserAccessLevel, kickUser, getUserPremium, getUserMute, setChatMute, getUserBan, getUserWarns, whoiscached, \
    scanURLMalware, scanURLRedirect, scanURLShortened, messagereply, deleteMessages
from config.config import api
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('kick'))
async def kick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        return await messagereply(message, disable_mentions=1, message=messages.kick_hint())
    if id == uid:
        return await messagereply(message, disable_mentions=1, message=messages.kick_myself())

    if await isChatAdmin(id, chat_id):
        return await messagereply(message, disable_mentions=1, message=messages.kick_access(
            id, await getUserName(id), await getUserNickname(id, chat_id)))

    uacc = await getUserAccessLevel(uid, chat_id)
    if await getUserAccessLevel(id, chat_id) >= uacc:
        return await messagereply(message, disable_mentions=1, message=messages.kick_higher())

    kick_cause = ' '.join(message.text.split()[1 + (not message.reply_message):])
    await messagereply(message, disable_mentions=1, message=messages.kick(
        await getUserName(uid), await getUserNickname(uid, chat_id), uid, await getUserName(id),
        await getUserNickname(id, chat_id), id, kick_cause if kick_cause else 'Причина не указана') if await kickUser(
        id, chat_id) else messages.kick_error())


@bl.chat_message(SearchCMD('mkick'))
async def mkick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if not await getUserPremium(uid):
        return await messagereply(message, disable_mentions=1, message=messages.no_prem())

    ids = []
    for i in message.text.split()[1:]:
        if id := await getIDFromMessage(i, None, 1):
            ids.append(id)
    if not ids:
        return await messagereply(message, disable_mentions=1, message=messages.mkick_error())

    names = await api.users.get(user_ids=ids)
    u_acc = await getUserAccessLevel(uid, chat_id)
    kick_res_count = 0
    msg = ''
    for ind, id in enumerate(ids):
        if u_acc <= await getUserAccessLevel(id, chat_id) or not await kickUser(id, chat_id):
            continue
        ch_nickname = await getUserNickname(id, chat_id)
        msg += f'➖ [id{id}|{ch_nickname if ch_nickname else f"{names[ind].first_name} {names[ind].last_name}"}]\n'
        kick_res_count += 1
    if kick_res_count > 0:
        return await messagereply(message, disable_mentions=1,
                                  message=f'💬 Пользователь [id{uid}|{await getUserName(uid)}] исключил '
                                          f'следующих пользователей из данной беседы:\n' + msg)
    await messagereply(message, disable_mentions=1, message=messages.mkick_no_kick())


@bl.chat_message(SearchCMD('mute'))
async def mute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await messagereply(message, disable_mentions=1, message=messages.mute_hint())
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())
    if id == uid:
        return await messagereply(message, disable_mentions=1, message=messages.mute_myself())

    try:
        if (mute_time := int(data[1 + (not message.reply_message)])) < 1:
            raise Exception
    except:
        return await messagereply(message, disable_mentions=1, message=messages.mute_hint())

    if mute_time == id:
        return await messagereply(message, disable_mentions=1, message=messages.mute_hint())

    if await getUserAccessLevel(id, chat_id) >= await getUserAccessLevel(uid, chat_id):
        return await messagereply(message, disable_mentions=1, message=messages.mute_higher())

    if (ch_mute := await getUserMute(id, chat_id)) >= time.time():
        return await messagereply(message, disable_mentions=1, message=messages.already_muted(
            await getUserName(id), await getUserNickname(id, chat_id), id, ch_mute))

    mute_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')

    async with (await pool()).acquire() as conn:
        ms = await conn.fetchrow('select last_mutes_times, last_mutes_causes, last_mutes_names, last_mutes_dates '
                                 'from mute where chat_id=$1 and uid=$2', chat_id, id)
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

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
                'update mute set mute = $1, last_mutes_times = $2, last_mutes_causes = $3, last_mutes_names = $4, '
                'last_mutes_dates = $5 where chat_id=$6 and uid=$7 returning 1', time.time() + mute_time,
                f"{mute_times}", f"{mute_causes}", f"{mute_names}", f"{mute_dates}", chat_id, id):
            await conn.execute(
                'insert into mute (uid, chat_id, mute, last_mutes_times, last_mutes_causes, last_mutes_names, '
                'last_mutes_dates) VALUES ($1, $2, $3, $4, $5, $6, $7)', id, chat_id, time.time() + mute_time,
                f"{mute_times}", f"{mute_causes}", f"{mute_names}", f"{mute_dates}")

    await setChatMute(id, chat_id, mute_time)
    await messagereply(message, disable_mentions=1, message=messages.mute(
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
        return await messagereply(message, disable_mentions=1, message=messages.warn_hint())
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())
    if id == uid:
        return await messagereply(message, disable_mentions=1, message=messages.warn_myself())
    if await getUserAccessLevel(id, chat_id) >= await getUserAccessLevel(uid, chat_id):
        return await messagereply(message, disable_mentions=1, message=messages.warn_higher())

    async with (await pool()).acquire() as conn:
        res = await conn.fetchrow('select warns, last_warns_times, last_warns_causes, last_warns_names, '
                                  'last_warns_dates from warn where chat_id=$1 and uid=$2', chat_id, id)
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

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
                'update warn set warns = $1, last_warns_times = $2, last_warns_causes = $3, last_warns_names = $4, '
                'last_warns_dates = $5 where chat_id=$6 and uid=$7 returning 1',
                warns, f"{warn_times}", f"{warn_causes}", f"{warn_names}", f"{warn_dates}", chat_id, id):
            await conn.execute(
                'insert into warn (uid, chat_id, warns, last_warns_times, last_warns_causes, last_warns_names, '
                'last_warns_dates) VALUES ($1, $2, $3, $4, $5, $6, $7)',
                id, chat_id, warns, f"{warn_times}", f"{warn_causes}", f"{warn_names}", f"{warn_dates}")
    await messagereply(message, disable_mentions=1, message=msg, keyboard=keyboard.punish_unpunish(
        uid, id, 'warn', message.conversation_message_id))


@bl.chat_message(SearchCMD('clear'))
async def clear(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id

    deleting = []
    for i in (message.fwd_messages + [message.reply_message]) if message.reply_message else message.fwd_messages:
        deleting.append((i.from_id, i.conversation_message_id))
    # data = message.text.split()
    # if (len(data) < 2 and not deleting) or (len(data) == 2 and not data[1].isdigit()) or (
    #         len(data) == 3 and not (id := await getIDFromMessage(message.text, None,) and not data[2].isdigit())):
    if not deleting:
        return await messagereply(message, disable_mentions=1, message=messages.clear_hint())
    deleting = [
        i for i in deleting if await getUserAccessLevel(i[0], chat_id) <= await getUserAccessLevel(uid, chat_id)]
    if deleting:
        try:
            deleted = await deleteMessages(
                chat_id=chat_id, cmids=[mid for _, mid in deleting])
            if all(True if i.error and 'admin message' in i.error.description else False for i in deleted):
                return await messagereply(message, disable_mentions=1, message=messages.clear_admin())
            if all(True if i.error else False for i in deleted):
                return await messagereply(message, disable_mentions=1, message=messages.clear_old())
            deleted = [i.conversation_message_id for i in deleted if i.error]
            deleting = [i[0] for i in deleting if i[1] not in deleted]
        except VKAPIError[15]:
            await messagereply(message, disable_mentions=1, message=messages.clear_admin())
        except VKAPIError:
            await messagereply(message, disable_mentions=1, message=messages.clear_old())
        else:
            await messagereply(message, disable_mentions=1, message=await messages.clear(deleting, uid, chat_id), keyboard=keyboard.deletemessages(uid, [message.conversation_message_id]))
    else:
        await messagereply(message, disable_mentions=1, message=messages.clear_higher())


@bl.chat_message(SearchCMD('snick'))
async def snick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id or len(data) <= 1:
        return await messagereply(message, disable_mentions=1, message=messages.snick_hint())
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())

    nickname = ' '.join(data[1 + (not message.reply_message):])
    if len(nickname) <= 0:
        return await messagereply(message, disable_mentions=1, message=messages.snick_hint())
    if len(nickname) >= 46 or '[' in nickname or ']' in nickname:
        return await messagereply(message, disable_mentions=1, message=messages.snick_too_long_nickname())

    if await getUserAccessLevel(id, chat_id) > await getUserAccessLevel(uid, chat_id):
        return await messagereply(message, disable_mentions=1, message=messages.snick_higher())

    oldnickname = await getUserNickname(id, chat_id)
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
                'update nickname set nickname = $1 where chat_id=$2 and uid=$3 returning 1', nickname, chat_id, id):
            await conn.execute(
                'insert into nickname (uid, chat_id, nickname) VALUES ($1, $2, $3)', id, chat_id, nickname)

    await messagereply(message, disable_mentions=1, message=messages.snick(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), id, await getUserName(id),
        oldnickname, nickname))


@bl.chat_message(SearchCMD('rnick'))
async def rnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await messagereply(message, disable_mentions=1, message=messages.snick_hint())
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())

    if await getUserAccessLevel(id, chat_id) > await getUserAccessLevel(uid, chat_id):
        return await messagereply(message, disable_mentions=1, message=messages.rnick_higher())
    if not (ch_nickname := await getUserNickname(id, chat_id)):
        return await messagereply(message, disable_mentions=1, message=messages.rnick_user_has_no_nick())

    async with (await pool()).acquire() as conn:
        await conn.execute('delete from nickname where chat_id=$1 and uid=$2', chat_id, id)
    await messagereply(message, disable_mentions=1, message=messages.rnick(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), id, await getUserName(id), ch_nickname))


@bl.chat_message(SearchCMD('nlist'))
async def nlist(message: Message):
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            'select uid, nickname from nickname where chat_id=$1 and uid>0 and uid=ANY($2) and nickname is not null'
            ' order by nickname', message.peer_id - 2000000000, [i.member_id for i in (
                await api.messages.get_conversation_members(peer_id=message.peer_id)).items])
    count = len(res)
    res = res[:30]
    await messagereply(message, disable_mentions=1, message=messages.nlist(
        res, await api.users.get(user_ids=[i[0] for i in res])), keyboard=keyboard.nlist(message.from_id, 0, count))


@bl.chat_message(SearchCMD('getnick'))
async def getnick(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(message, disable_mentions=1, message=messages.getnick_hint())
    query = ' '.join(data[1:])
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            "select uid, nickname from nickname where chat_id=$1 and uid>0 and uid=ANY($2) and lower(nickname) "
            "like $3 order by nickname limit 30", chat_id, [i.member_id for i in (
                await api.messages.get_conversation_members(peer_id=message.peer_id)).items],
            '%%' + query.lower() + '%%')
    if not res:
        return await messagereply(message, disable_mentions=1, message=messages.getnick_no_result(query))
    await messagereply(message, disable_mentions=1, message=await messages.getnick(res, query))


@bl.chat_message(SearchCMD('staff'))
async def staff(message: Message):
    chat_id = message.peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            'select uid, access_level from accesslvl where chat_id=$1 and uid>0 and access_level>0 and '
            'access_level<8 order by access_level desc', chat_id)
    await messagereply(message, disable_mentions=1, message=await messages.staff(
        res, await api.users.get(user_ids=[i[0] for i in res if i[0] > 0]), chat_id))


@bl.chat_message(SearchCMD('olist'))
async def olist(message: Message):
    members = await api.users.get(user_ids=[f'{i.member_id}' for i in (
        await api.messages.get_conversation_members(peer_id=message.peer_id - 2000000000 + 2000000000)).items],
                                  fields='online')
    members_online = {}
    for i in members:
        if i.online:
            if i.online_mobile:
                online_mobile = True
            else:
                online_mobile = False
            members_online[f'[id{i.id}|{i.first_name} {i.last_name}]'] = online_mobile
    await messagereply(message, disable_mentions=1, message=messages.olist(members_online))


@bl.chat_message(SearchCMD('check'))
async def check(message: Message):
    chat_id = message.peer_id - 2000000000
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await messagereply(message, disable_mentions=1, message=messages.check_help())
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())

    ban = await getUserBan(id, chat_id) - time.time()
    mute = await getUserMute(id, chat_id) - time.time()
    msg = messages.check(id, await getUserName(id), await getUserNickname(id, chat_id),
                         ban if ban > 0 else 0, await getUserWarns(id, chat_id), mute if mute > 0 else 0)
    kb = keyboard.check(message.from_id, id)
    await messagereply(message, disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('scan'))
async def scan(message: Message):
    data = message.text.split()
    if len(data) < 2 and not message.reply_message:
        return await messagereply(message, disable_mentions=1, message=messages.scan_hint())
    links = set()
    for i in (message.reply_message.text.split() + data[1:]) if message.reply_message else data[1:]:
        for y in i.split('/'):
            if not whoiscached(y):
                continue
            links.add(i if '://' in i else 'https://' + i)
    if not links:
        return await messagereply(message, disable_mentions=1, message=messages.scan_hint())
    await messagereply(message, disable_mentions=1, message=''.join([messages.scan(
        i, scanURLMalware(i), scanURLRedirect(i), scanURLShortened(i)) + '\n\n' for i in links]))


@bl.chat_message(SearchCMD('invited'))
async def invited(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        id = message.from_id
    async with (await pool()).acquire() as conn:
        invites = await conn.fetchval(
            'select count(*) as c from refferal where from_id=$1 and chat_id=$2', id, message.chat_id)
    await messagereply(message, disable_mentions=1, message=messages.invites(
        id, await getUserName(id), await getUserNickname(id, message.chat_id), invites))
