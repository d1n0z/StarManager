import time
from ast import literal_eval
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.rules import SearchCMD
from Bot.utils import getUserName, kickUser, getUserNickname, getIDFromMessage, getUserAccessLevel, getUserBan
from config.config import API
from db import SilenceMode, LastMessageDate, Ban

bl = BotLabeler()


@bl.chat_message(SearchCMD('timeout'))
async def timeout(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) != 2:
        msg = messages.timeout_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if int(data[1]) not in [0, 1]:
        msg = messages.timeout_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    sm = SilenceMode.get_or_create(chat_id=chat_id)[0]
    sm.time = data[1]
    sm.save()

    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    if int(data[1]) == 1:
        msg = messages.timeouton(uid, u_name, u_nickname)
    else:
        msg = messages.timeoutoff(uid, u_name, u_nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('inactive'))
async def inactive(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) != 2:
        msg = messages.inactive_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    count = data[1]
    if count.isdigit():
        count = int(count)
    else:
        count = 0
    if count is None or count <= 0:
        msg = messages.inactive_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    count = time.time() - count * 86400
    res = LastMessageDate.select().where(LastMessageDate.chat_id == chat_id, LastMessageDate.uid > 0,
                                         LastMessageDate.last_message < count)
    kicked = 0
    if len(res) <= 0:
        msg = messages.inactive_no_results()
        await message.reply(disable_mentions=1, message=msg)
        return
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = [i.member_id for i in members.items if i.member_id > 0]
    for i in res:
        if i.uid in members:
            try:
                x = await kickUser(i.uid, chat_id)
                kicked += x
            except:
                pass
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.inactive(uid, u_name, u_nickname, kicked)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('ban'))
async def ban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message)
    if id == uid:
        msg = messages.ban_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.ban_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    if message.reply_message is None:
        if len(data) == 2:
            ban_time = 3650 * 86400
            ban_cause = None
        else:
            if data[2].isdigit():
                ban_time = int(data[2]) * 86400
                if ban_time > 86400 * 3650:
                    msg = messages.ban_maxtime()
                    await message.reply(disable_mentions=1, message=msg)
                    return
                ban_cause = None if len(data) == 3 else ' '.join(data[3:])
            else:
                ban_time = 3650 * 86400
                ban_cause = ' '.join(data[2:])
    else:
        if len(data) == 1:
            ban_time = 3650 * 86400
            ban_cause = None
        else:
            if data[1].isdigit():
                ban_time = int(data[1]) * 86400
                if ban_time > 86400 * 3650:
                    msg = messages.ban_maxtime()
                    await message.reply(disable_mentions=1, message=msg)
                    return
                ban_cause = None if len(data) == 2 else ' '.join(data[2:])
            else:
                ban_time = 3650 * 86400
                ban_cause = ' '.join(data[1:])

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc >= u_acc:
        msg = messages.ban_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_name = await getUserName(id)
    ch_nickname = await getUserNickname(id, chat_id)
    ch_ban = await getUserBan(id, chat_id)
    if ch_ban >= time.time():
        msg = messages.already_banned(ch_name, ch_nickname, id, ch_ban)
        await message.reply(disable_mentions=1, message=msg)
        return

    ban_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
    res = Ban.get_or_none(Ban.chat_id == chat_id, Ban.uid == id)
    if res is not None:
        ban_times = literal_eval(res.last_bans_times)
        ban_causes = literal_eval(res.last_bans_causes)
        ban_names = literal_eval(res.last_bans_names)
        ban_dates = literal_eval(res.last_bans_dates)
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

    b = Ban.get_or_create(uid=id, chat_id=chat_id)[0]
    b.ban = int(time.time()) + ban_time
    b.last_bans_times = f"{ban_times}"
    b.last_bans_causes = f"{ban_causes}"
    b.last_bans_names = f"{ban_names}"
    b.last_bans_dates = f"{ban_dates}"
    b.save()

    msg = messages.ban(uid, u_name, u_nickname, id, ch_name, ch_nickname, ban_cause, ban_time // 86400)
    kick = await kickUser(id, chat_id)
    if not kick:
        msg += '\n❗ Пользователя не удалось кикнуть'
    await message.reply(disable_mentions=1, message=msg)
    return


@bl.chat_message(SearchCMD('unban'))
async def unban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message)
    if id == uid:
        msg = messages.unban_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.unban_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    ch_ban = await getUserBan(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc >= u_acc:
        msg = messages.unban_higher()
        await message.reply(disable_mentions=1, message=msg)
        return
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    name = await getUserName(id)
    ch_nickname = await getUserNickname(id, chat_id)
    if ch_ban <= time.time():
        msg = messages.unban_no_ban(id, name, ch_nickname)
        await message.reply(disable_mentions=1, message=msg)
        return
    b = Ban.get_or_none(Ban.uid == id, Ban.chat_id == chat_id)
    if b is not None:
        b.ban = 0
        b.save()
    msg = messages.unban(u_name, u_nickname, uid, name, ch_nickname, id)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('banlist'))
async def banlist(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    res = Ban.select().where(Ban.ban > int(time.time()), Ban.chat_id == chat_id)
    count = len(res)
    res = res.limit(30)[::-1]
    names = await API.users.get(user_ids=[i.uid for i in res])
    msg = await messages.banlist(res, names, count)
    kb = keyboard.banlist(uid, 0)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('zov'))
async def zov(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = [s for s in message.text.split(' ') if s]
    if len(data) <= 1:
        msg = messages.zov_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    cause = ' '.join(data[1:])
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    u_name = await getUserName(uid)
    u_nick = await getUserNickname(uid, chat_id)
    msg = messages.zov(uid, u_name, u_nick, cause, members)
    await message.reply(message=msg)


@bl.chat_message(SearchCMD('kickmenu'))
async def kickmenu(message: Message):
    uid = message.from_id
    kb = keyboard.kickmenu(uid)
    msg = messages.kickmenu()
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)
