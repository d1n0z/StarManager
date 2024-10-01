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
from db import Mute, Warn, Nickname, AccessLevel

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

    ms = Mute.get_or_none(Mute.uid == id, Mute.chat_id == chat_id)
    if ms is not None and None not in (ms.last_mutes_times, ms.last_mutes_causes,
                                       ms.last_mutes_names, ms.last_mutes_dates):
        mute_times = literal_eval(ms.last_mutes_times)
        mute_causes = literal_eval(ms.last_mutes_causes)
        mute_names = literal_eval(ms.last_mutes_names)
        mute_dates = literal_eval(ms.last_mutes_dates)
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

    ms = Mute.get_or_create(uid=id, chat_id=chat_id)[0]
    ms.mute = int(time.time()) + mute_time
    ms.last_mutes_times = f"{mute_times}"
    ms.last_mutes_causes = f"{mute_causes}"
    ms.last_mutes_names = f"{mute_names}"
    ms.last_mutes_dates = f"{mute_dates}"
    ms.save()

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
    res = Warn.get_or_none(Warn.chat_id == chat_id, Warn.uid == id)
    if res is not None:
        warns = res.warns + 1
        warn_times = literal_eval(res.last_warns_times)
        warn_causes = literal_eval(res.last_warns_causes)
        warn_names = literal_eval(res.last_warns_names)
        warn_dates = literal_eval(res.last_warns_dates)
    else:
        warns = 1
        warn_times = []
        warn_causes = []
        warn_names = []
        warn_dates = []
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
    w = Warn.get_or_create(chat_id=chat_id, uid=id)[0]
    w.warns = warns
    w.last_warns_times = f"{warn_times}"
    w.last_warns_causes = f"{warn_causes}"
    w.last_warns_names = f"{warn_names}"
    w.last_warns_dates = f"{warn_dates}"
    w.save()

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
            u_ids.remove(i)
            cmids.remove(cmids[ind])
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

    n = Nickname.get_or_create(uid=id, chat_id=chat_id)[0]
    n.nickname = nickname
    n.save()

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

    n = Nickname.get_or_none(Nickname.uid == id, Nickname.chat_id == chat_id)
    if n is not None:
        n.delete_instance()
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
    res = Nickname.select().where(Nickname.chat_id == chat_id, Nickname.uid > 0, Nickname.uid << members_uid,
                                  Nickname.nickname.is_null(False)).order_by(Nickname.nickname)
    count = len(res)
    res = res[:30]
    names = await API.users.get(user_ids=[i.uid for i in res])
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
    res = Nickname.select().where(Nickname.uid > 0, Nickname.chat_id == chat_id,
                                  Nickname.nickname.contains(query)).order_by(Nickname.nickname).limit(30)
    lres = len(res)
    names = await API.users.get(user_ids=[f'{i.uid}' for i in res])
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
    res = AccessLevel.select().where(AccessLevel.uid > 0, AccessLevel.access_level > 0,
                                     AccessLevel.chat_id == chat_id).order_by(AccessLevel.access_level)
    names = await API.users.get(user_ids=[f'{i.uid}' for i in res])
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
