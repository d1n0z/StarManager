import time
from ast import literal_eval
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.utils import getSilence
from Bot.rules import SearchCMD
from Bot.utils import (getUserName, kickUser, getUserNickname, getIDFromMessage, getUserAccessLevel, getUserBan,
                       messagereply)
from config.config import api
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('timeout'))
async def timeout(message: Message):
    activated = await getSilence(message.peer_id - 2000000000)
    await messagereply(message, disable_mentions=1, message=messages.timeout(activated),
                       keyboard=keyboard.timeout(message.from_id, activated))


@bl.chat_message(SearchCMD('inactive'))
async def inactive(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(message, disable_mentions=1, message=messages.inactive_hint())
    count = data[1]
    if not count.isdigit() or (count := int(count)) <= 0:
        return await messagereply(message, disable_mentions=1, message=messages.inactive_hint())
    count = time.time() - count * 86400
    async with (await pool()).acquire() as conn:
        res = await conn.fetch('select uid from lastmessagedate where chat_id=$1 and uid>0 and last_message<$2',
                               chat_id, count)
    kicked = 0
    if len(res) <= 0:
        return await messagereply(message, disable_mentions=1, message=messages.inactive_no_results())
    members = await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = [i.member_id for i in members.items if i.member_id > 0]
    for i in res:
        if i[0] in members:
            try:
                x = await kickUser(i[0], chat_id)
                kicked += x
            except:
                pass
    await messagereply(message, disable_mentions=1, message=messages.inactive(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), kicked))


@bl.chat_message(SearchCMD('ban'))
async def ban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        return await messagereply(message, disable_mentions=1, message=messages.ban_myself())
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(message, disable_mentions=1, message=messages.ban_hint())
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())

    if message.reply_message is None:
        if len(data) == 2:
            ban_time = 3650 * 86400
            ban_cause = None
        else:
            if data[2].isdigit():
                ban_time = int(data[2]) * 86400
                if ban_time > 86400 * 3650:
                    msg = messages.ban_maxtime()
                    await messagereply(message, disable_mentions=1, message=msg)
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
                    await messagereply(message, disable_mentions=1, message=msg)
                    return
                ban_cause = None if len(data) == 2 else ' '.join(data[2:])
            else:
                ban_time = 3650 * 86400
                ban_cause = ' '.join(data[1:])
    if ban_time <= 0:
        return await messagereply(message, disable_mentions=1, message=messages.ban_hint())

    if await getUserAccessLevel(id, chat_id) >= await getUserAccessLevel(uid, chat_id):
        return await messagereply(message, disable_mentions=1, message=messages.ban_higher())

    if (ch_ban := await getUserBan(id, chat_id)) >= time.time():
        return await messagereply(message, disable_mentions=1, message=messages.already_banned(
            await getUserName(id), await getUserNickname(id, chat_id), id, ch_ban))

    ban_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
    async with (await pool()).acquire() as conn:
        res = await conn.fetchrow(
            'select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates from ban where '
            'chat_id=$1 and uid=$2', chat_id, id)
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
    u_name = await getUserName(uid)
    ban_names.append(f'[id{uid}|{u_name}]')
    ban_dates.append(ban_date)

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
                'update ban set ban = $1, last_bans_times = $2, last_bans_causes = $3, last_bans_names = $4, '
                'last_bans_dates = $5 where chat_id=$6 and uid=$7 returning 1', time.time() + ban_time,
                f"{ban_times}", f"{ban_causes}", f"{ban_names}", f"{ban_dates}", chat_id, id):
            await conn.execute(
                'insert into ban (uid, chat_id, ban, last_bans_times, last_bans_causes, last_bans_names, '
                'last_bans_dates) values ($1, $2, $3, $4, $5, $6, $7)', id, chat_id,
                time.time() + ban_time, f"{ban_times}", f"{ban_causes}", f"{ban_names}", f"{ban_dates}")

    await messagereply(message, disable_mentions=1, message=messages.ban(
        uid, u_name, await getUserNickname(uid, chat_id), id, await getUserName(id), await getUserNickname(id, chat_id),
        ban_cause, ban_time // 86400) + (
        '\n❗ Пользователя не удалось кикнуть' if not await kickUser(id, chat_id) else ''),
                        keyboard=keyboard.punish_unpunish(uid, id, 'ban', message.conversation_message_id))
    return


@bl.chat_message(SearchCMD('unban'))
async def unban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        return await messagereply(message, disable_mentions=1, message=messages.unban_myself())
    if (len(data) == 1 and message.reply_message is None) or not id:
        return await messagereply(message, disable_mentions=1, message=messages.unban_hint())
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())

    if await getUserAccessLevel(id, chat_id) >= await getUserAccessLevel(uid, chat_id):
        return await messagereply(message, disable_mentions=1, message=messages.unban_higher())
    if await getUserBan(id, chat_id) <= time.time():
        return await messagereply(message, disable_mentions=1, message=messages.unban_no_ban(
            id, await getUserName(id), await getUserNickname(id, chat_id)))
    async with (await pool()).acquire() as conn:
        await conn.execute('update ban set ban = 0 where chat_id=$1 and uid=$2', chat_id, id)
    await messagereply(message, disable_mentions=1, message=messages.unban(
        await getUserName(uid), await getUserNickname(uid, chat_id), uid, await getUserName(id),
        await getUserNickname(id, chat_id), id))


@bl.chat_message(SearchCMD('banlist'))
async def banlist(message: Message):
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            'select uid, chat_id, last_bans_causes, ban, last_bans_names from ban where chat_id=$1 and '
            'ban>$2 order by uid desc', message.peer_id - 2000000000, time.time())
    count = len(res)
    res = res[:30]
    await messagereply(message, disable_mentions=1, message=await messages.banlist(
        res, count), keyboard=keyboard.banlist(
        message.from_id, 0, count))


@bl.chat_message(SearchCMD('zov'))
async def zov(message: Message):
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(message, disable_mentions=1, message=messages.zov_hint())
    await messagereply(message, message=messages.zov(
        uid, await getUserName(uid), await getUserNickname(uid, message.peer_id - 2000000000), ' '.join(data[1:]),
        (await api.messages.get_conversation_members(peer_id=message.peer_id)).items))


@bl.chat_message(SearchCMD('kickmenu'))
async def kickmenu(message: Message):
    await messagereply(message, disable_mentions=1, message=messages.kickmenu(),
                       keyboard=keyboard.kickmenu(message.from_id))
