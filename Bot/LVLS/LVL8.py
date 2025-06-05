import asyncio
import os
import statistics
import time
import traceback
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import getUInfBanned
from Bot.rules import SearchCMD
from Bot.scheduler import backup
from Bot.utils import getUserName, getIDFromMessage, getUserNickname, sendMessage, addUserXP, getChatName, \
    setUserAccessLevel, pointWords, chunks, getURepBanned, messagereply, kickUser
from config.config import api, GROUP_ID, DEVS, PATH
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('getdev'))
async def getdev_handler(message: Message):
    uid = message.from_id
    if uid in DEVS:
        await setUserAccessLevel(uid, message.peer_id - 2000000000, 8)


@bl.chat_message(SearchCMD('backup'))
async def backup_handler(message: Message):
    await backup()
    await messagereply(message, '💚 Completed.')


@bl.chat_message(SearchCMD('botinfo'))
async def botinfo(message: Message):
    # completely broken(and bad), too lazy to fix
    await messagereply(message, disable_mentions=1, message='Эта команда отключена.')
    # chat_id = message.peer_id - 2000000000
    # chats = []
    # for i in ac.select().where(ac.access_level > 6):
    #     if i.chat_id not in chats:
    #         chats.append(i.chat_id)
    # total_users = 0
    # premium_users = 0
    # users = []
    #
    # biggest_chat_owner_id = None
    # biggest_chat_owner_name = None
    # biggest_chat_users = 0
    # biggest_chat_id = 0
    # for i in chats:
    #     chat_users = await api.messages.get_conversation_members(i + 2000000000, group_id=GROUP_ID)
    #     chat_users = chat_users.items
    #     owner = None
    #     for u in chat_users:
    #         if u.member_id not in users:
    #             users.append(u.member_id)
    #             if u.is_owner:
    #                 owner = u.member_id
    #     if len(chat_users) > biggest_chat_users:
    #         biggest_chat_owner_id = owner
    #         biggest_chat_owner_name = await getUserName(owner)
    #         biggest_chat_users = len(chat_users)
    #         biggest_chat_id = chat_id
    #     total_users += len(chat_users)
    #
    # premium_pool = getPremium()
    # premium_users += len(premium_pool.select())
    #
    # chgroups = getChatGroups()
    # groups = chgroups.select()
    #
    # all_groups = []
    # grlens = {}
    #
    # for u in groups:
    #     if u.group not in all_groups:
    #         all_groups.append(u.group)
    #
    # for g in all_groups:
    #     grlens[g] = len(chgroups.select().where(chgroups.group == g))
    #
    # max_group_name = list(grlens.keys())[list(grlens.keys()).index(max(grlens.items(),key=operator.itemgetter(1))[0])]
    # max_group_count = grlens[max_group_name]
    #
    # gpool_table = getGPool()
    # gpools = gpool_table.select()
    #
    # gplens = {}
    # for gpool in gpools:
    #     try:
    #         gplens[gpool.uid] += 1
    #     except KeyError:
    #         gplens[gpool.uid] = 1
    # biggest_gpool = list(gplens.keys())[list(gplens.keys()).index(max(gplens.items(), key=operator.itemgetter(1))[0])]
    # max_pool = gplens[biggest_gpool]
    #
    # u_name = await api.users.get(user_ids=746110579)
    # biggest_gpool_owner_name = f"{u_name[0].first_name} {u_name[0].last_name}"
    # msg = messages.bot_info(chats, total_users, users, premium_users, all_groups, biggest_gpool,
    #                         biggest_gpool_owner_name, max_pool, max_group_name, max_group_count, biggest_chat_id,
    #                         biggest_chat_users, biggest_chat_owner_id, biggest_chat_owner_name)
    # await messagereply(message, msg)


@bl.chat_message(SearchCMD('msg'))
async def msg(message: Message):
    data = message.text.split()
    if len(data) <= 1:
        return await messagereply(message, messages.msg_hint())
    devmsg = ' '.join(data[1:])
    msg = messages.msg(devmsg)
    k = 0
    async with (await pool()).acquire() as conn:
        chats = await conn.fetch('select chat_id from allchats')
    print(len(chats))
    for i in chunks(chats, 2500):
        try:
            code = ''
            for y in chunks(i, 100):
                code += ('API.messages.send({"random_id": 0, "peer_ids": [' + ','.join(str(o[0]) for o in y) +
                         '], "message": "' + f"{msg}" + '"});')
            await api.execute(code=code)
            k += len(i)
            print(f'sent {k}/{len(chats)}')
            await asyncio.sleep(1)
        except:
            traceback.print_exc()
    msg = f'done {k}/{len(chats)}'
    print(msg)
    await messagereply(message, msg)


@bl.chat_message(SearchCMD('addblack'))
async def addblack(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        return await messagereply(message, messages.addblack_hint())
    if id == uid:
        return await messagereply(message, messages.addblack_myself())
    if id < 0:
        return await messagereply(message, messages.id_group())
    async with (await pool()).acquire() as conn:
        await conn.execute('insert into blacklist (uid) values ($1) on conflict (uid) do nothing', id)
    dev_name = await getUserName(uid)
    dev_nickname = await getUserNickname(uid, chat_id)
    await messagereply(message, messages.addblack(uid, dev_name, dev_nickname, id, await getUserName(id),
                                                  await getUserNickname(id, chat_id)))
    await sendMessage(id, messages.blacked(uid, dev_name, dev_nickname))


@bl.chat_message(SearchCMD('delblack'))
async def delblack(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        return await messagereply(message, messages.delblack_hint())
    if id == uid:
        return await messagereply(message, messages.delblack_myself())
    if id < 0:
        return await messagereply(message, messages.id_group())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('delete from blacklist where uid=$1 returning 1', id):
            return await messagereply(message, messages.delblack_no_user(
                id, await getUserName(id), await getUserNickname(id, chat_id)))
    dev_name = await getUserName(uid)
    dev_nickname = await getUserNickname(uid, chat_id)
    await messagereply(message, messages.delblack(uid, dev_name, dev_nickname, id, await getUserName(id),
                                                  await getUserNickname(id, chat_id)))
    await sendMessage(id, messages.delblacked(uid, dev_name, dev_nickname))


@bl.chat_message(SearchCMD('blacklist'))
async def blacklist(message: Message):
    users = {}
    async with (await pool()).acquire() as conn:
        blc = await conn.fetch('select uid from blacklist')
    for user in blc:
        users[await getUserName(user[0])] = user[0]
    msg = f'⚛ Список пользователей в ЧС бота (Всего : {len(list(users))})\n\n'
    for k, i in users.items():
        msg += f"➖ {i} : | [id{i}|{k}]\n"
    await messagereply(message, msg)


@bl.chat_message(SearchCMD('setstatus'))
async def setstatus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    data = message.text.split()
    if id == 0 or not data[2].isdigit():
        return await messagereply(message, messages.setstatus_hint())
    if id < 0:
        return await messagereply(message, messages.id_group())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
                'update premium set time = $1 where uid=$2 returning 1', time.time() + int(data[2]) * 86400, id):
            await conn.execute(
                'insert into premium (uid, time) values ($1, $2)', id, time.time() + int(data[2]) * 86400)

    dev_name = await getUserName(uid)
    await messagereply(message, messages.setstatus(uid, dev_name, await getUserNickname(uid, chat_id),
                                                   id, await getUserName(id), await getUserNickname(id, chat_id)))
    await sendMessage(id, messages.ugiveStatus(id, await getUserNickname(id, chat_id), await getUserName(id),
                                               uid, await getUserNickname(uid, chat_id), dev_name, data[2]))


@bl.chat_message(SearchCMD('delstatus'))
async def delstatus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        return await messagereply(message, messages.delstatus_hint())
    if id < 0:
        return await messagereply(message, messages.id_group())
    async with (await pool()).acquire() as conn:
        await conn.execute('delete from premium where uid=$1', id)

    dev_name = await getUserName(uid)
    await messagereply(message, messages.delstatus(uid, dev_name, await getUserNickname(uid, chat_id),
                                                   id, await getUserName(id), await getUserNickname(id, chat_id)))
    await sendMessage(id, messages.udelStatus(uid, dev_name))


@bl.chat_message(SearchCMD('statuslist'))
async def statuslist(message: Message):
    async with (await pool()).acquire() as conn:
        prem = await conn.fetch('select uid, time from premium')
    await messagereply(
        message, await messages.statuslist(prem), keyboard=keyboard.statuslist(message.from_id, 0, len(prem)))


@bl.chat_message(SearchCMD('setprem'))
async def setprem(message: Message):
    uid = message.from_id
    chat_id = await getIDFromMessage(message.text, message.reply_message)
    if chat_id <= 0:
        return await messagereply(message, messages.setprem_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('update publicchats set premium = true where chat_id=$1 returning 1', chat_id):
            await conn.execute(
                'insert into publicchats (chat_id, premium, isopen) values ($1, true, false)', chat_id)

    await messagereply(message, messages.setprem(chat_id))
    await sendMessage(message.peer_id, messages.premchat(uid, await getUserName(uid)))


@bl.chat_message(SearchCMD('delprem'))
async def delprem(message: Message):
    chat_id = await getIDFromMessage(message.text, message.reply_message)
    if chat_id <= 0:
        return await messagereply(message, messages.delprem_hint())
    async with (await pool()).acquire() as conn:
        await conn.execute('update publicchats set premium = false where chat_id=$1', chat_id)
    await messagereply(message, messages.delprem(chat_id))


@bl.chat_message(SearchCMD('premlist'))
async def permlist(message: Message):
    async with (await pool()).acquire() as conn:
        prem = await conn.fetch('select chat_id from publicchats where premium=true')
    await messagereply(message, messages.premlist(prem))


@bl.chat_message(SearchCMD('givexp'))
async def givexp(message: Message):
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await messagereply(message, '🔶 Пользователь не найден')
    data = message.text.split()
    await addUserXP(id, int(data[2]))
    await messagereply(message, messages.givexp(uid, await getUserName(uid), id, await getUserName(id), data[2]))


@bl.chat_message(SearchCMD('resetlvl'))
async def resetlvl(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await messagereply(message, '🔶 Пользователь не найден')
    async with (await pool()).acquire() as conn:
        await conn.execute('update xp set xp=0, lvl=0, league=1 where uid=$1', id)
    u_name = await getUserName(id)
    msgsent = messages.resetlvlcomplete(id, u_name)
    if await sendMessage(peer_ids=id, msg=messages.resetlvl(id, u_name)) is False:
        msgsent += '\n❗ Пользователю не удалось отправить сообщение'
    await messagereply(message, msgsent)


@bl.chat_message(SearchCMD('block'))
async def block(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if len(data) < 3 or data[1] not in ['chat', 'user'] or not id or id < 0:
        return await messagereply(message, messages.block_hint())
    reason = ' '.join(data[3:]) or None
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('select exists(select 1 from blocked where uid=$1 and type=$2)', id, data[1]):
            await conn.execute('insert into blocked (uid, type, reason) values ($1, $2, $3)', id, data[1], reason)
            if data[1] != 'chat':
                await conn.execute('delete from xp where uid=$1', id)
                await conn.execute('delete from premium where uid=$1', id)
                chats = set(
                    i[0] for i in await conn.fetch('select chat_id from userjoineddate where uid=$1', id)) or set()
                chats.update(i[0] for i in await conn.fetch('select chat_id from accesslvl where uid=$1', id))
                chats.update(i[0] for i in await conn.fetch('select chat_id from nickname where uid=$1', id))
                chats.update(i[0] for i in await conn.fetch('select chat_id from lastmessagedate where uid=$1', id))
    if data[1] == 'chat':
        await sendMessage(id + 2000000000, messages.block_chatblocked(id, reason),
                          keyboard.block_chatblocked())
        await api.messages.remove_chat_user(id, member_id=-GROUP_ID)
    else:
        await sendMessage(id, messages.block_userblocked(id, reason), keyboard.block_chatblocked())
        for i in chats:
            if await kickUser(id, i):
                await sendMessage(i + 2000000000, messages.block_blockeduserinvite(id, await getUserName(id), reason))
            await asyncio.sleep(0.3)
    await messagereply(message, messages.block())


@bl.chat_message(SearchCMD('unblock'))
async def unblock(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if len(data) != 3 or data[1] not in ['chat', 'user'] or not id:
        return await messagereply(message, messages.unblock_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('delete from blocked where uid=$1 and type=$2 returning 1', id, data[1]):
            return await messagereply(message, messages.unblock_noban())
    if data[1] == 'chat':
        await sendMessage(id + 2000000000, messages.block_chatunblocked(id))
    await messagereply(message, messages.unblock())


@bl.chat_message(SearchCMD('blocklist'))
async def blocklist(message: Message):
    async with (await pool()).acquire() as conn:
        inf = await conn.fetch("select uid, reason from blocked where type='user'")
    msg = f'⚛ Список пользователей в блокировке бота (Всего : {len(inf)})\n\n'
    for user in inf:
        msg += f"➖ [id{user[0]}|{await getUserName(user[0])}]" + (f' | {user[1]}' if user[1] else '') + "\n"
    await messagereply(message, msg, keyboard=keyboard.blocklist(message.from_id))


@bl.chat_message(SearchCMD('cmdcount'))
async def cmdcount(message: Message):
    async with (await pool()).acquire() as conn:
        cmdsraw = await conn.fetch(
            'select cmd, timestart, timeend from commandsstatistics where timeend is not null')
    cmds = {}
    for i in cmdsraw:
        if i[0] not in cmds:
            cmds[i[0]] = [i[2].timestamp() - i[1].timestamp()]
        else:
            cmds[i[0]].append(i[2].timestamp() - i[1].timestamp())
    msg = ''
    for i in cmds.keys():
        msg += f'{i}: {statistics.mean(cmds[i])} секунд | использован {len(cmds[i])} раз\n'
    await messagereply(message, disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('msgsaverage'))
async def msgsaverage(message: Message):
    async with (await pool()).acquire() as conn:
        msts = await conn.fetch('select timestart, timeend from messagesstatistics where timeend is not null')
    msgs = [i[1].timestamp() - i[0].timestamp() for i in msts]
    await messagereply(message, disable_mentions=1, message=f'Среднее время обработки - {statistics.mean(msgs)} секунд')


@bl.chat_message(SearchCMD('msgscount'))
async def msgscount(message: Message):
    now = datetime.now()
    async with (await pool()).acquire() as conn:
        msgs5minutes = await conn.fetchval(
            'select count(*) as c from messagesstatistics where timeend is not null and '
            'extract(minute from timestart)>=$1 and extract(hour from timestart)=$2 and '
            'extract(day from timestart)=$3 and extract(month from timestart)=$4 and '
            'extract(year from timestart)=$5', now.minute - 5, now.hour, now.day, now.month, now.year)
        msgsminute = await conn.fetchval(
            'select count(*) as c from messagesstatistics where timeend is not null and '
            'extract(minute from timestart)=$1 and extract(hour from timestart)=$2 and '
            'extract(day from timestart)=$3 and extract(month from timestart)=$4 and '
            'extract(year from timestart)=$5', now.minute, now.hour, now.day, now.month, now.year)
        msgshour = await conn.fetchval(
            'select count(*) as c from messagesstatistics where timeend is not null and '
            'extract(hour from timestart)=$1 and extract(day from timestart)=$2 and '
            'extract(month from timestart)=$3 and extract(year from timestart)=$4',
            now.hour, now.day, now.month, now.year)
        msgslasthour = await conn.fetchval(
            'select count(*) as c from messagesstatistics where timeend is not null and '
            'extract(hour from timestart)=$1 and extract(day from timestart)=$2 and '
            'extract(month from timestart)=$3 and extract(year from timestart)=$4',
            now.hour - 1, now.day, now.month, now.year)
        msgsday = await conn.fetchval(
            'select count(*) as c from messagesstatistics where timeend is not null and '
            'extract(day from timestart)=$1 and extract(month from timestart)=$2 and '
            'extract(year from timestart)=$3', now.day,  now.month, now.year)
        msgslastday = await conn.fetchval(
            'select count(*) as c from messagesstatistics where timeend is not null and '
            'extract(day from timestart)=$1 and extract(month from timestart)=$2 and '
            'extract(year from timestart)=$3', now.day - 1,  now.month, now.year)
    await messagereply(message, disable_mentions=1,
                       message=f'{msgslastday} сообщений за вчера\n'
                               f'{msgslasthour} сообщений за прошлый час\n'
                               f'{msgs5minutes} сообщений за последние 5 минут\n'
                               f'{msgsday} сообщений за сегодня\n'
                               f'{msgshour} сообщений за этот час\n'
                               f'{msgsminute} сообщений за эту минуту')


@bl.chat_message(SearchCMD('mwaverage'))
async def mwaverage(message: Message):
    async with (await pool()).acquire() as conn:
        mwst = await conn.fetch('select timestart, timeend from middlewaresstatistics where timeend is not null')
    average = statistics.mean([i[1].timestamp() - i[0].timestamp() for i in mwst])
    await messagereply(message, disable_mentions=1, message=f'Среднее время работы мидлвари - {average} секунд')


@bl.chat_message(SearchCMD('getlink'))
async def getlink(message: Message):
    data = message.text.lower().split()
    if len(data) != 2 or not data[1].isdigit():
        return await messagereply(message, '/getlink chat_id')
    try:
        await messagereply(message, (
            await api.messages.get_invite_link(peer_id=int(data[1]) + 2000000000, reset=0, group_id=GROUP_ID)).link)
    except:
        await messagereply(message, '❌ Невозможно сгенерировать ссылку')


@bl.chat_message(SearchCMD('reboot'))
async def reboot(message: Message):
    if len(data := message.text.split()) == 2:
        await messagereply(
            message, f'⌛ Перезагрузка произойдет через {pointWords(int(data[1]), ("минуту", "минуты", "минут"))}.')
        await asyncio.sleep(int(data[1]) * 60)
    async with (await pool()).acquire() as conn:
        await conn.execute(
            'insert into reboots (chat_id, time, sended) values ($1, $2, false)', message.chat_id, time.time())
    await messagereply(message, messages.reboot())
    os.system(PATH + 'startup.sh')  # noqa


@bl.chat_message(SearchCMD('sudo'))
async def sudo(message: Message):
    if 'reboot' in message.text:
        async with (await pool()).acquire() as conn:
            await conn.execute(
                'insert into reboots (chat_id, time, sended) values ($1, $2, false)', message.chat_id, time.time())
    await messagereply(message, os.popen(f'sudo {" ".join(message.text.split()[1:])}').read())


@bl.chat_message(SearchCMD('getuserchats'))
async def getuserchats(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await messagereply(message, '🔶 Пользователь не найден')
    limit = message.text.split()[-1]
    async with (await pool()).acquire() as conn:
        top = await conn.fetch('select chat_id, messages from messages where uid=$1 order by messages desc limit '
                               '$2', id, int(limit) if limit.isdigit() else 100)
    msg = '✝ Беседы пользователя:\n'
    for i in top:
        if await getUInfBanned(id, i[0]):
            continue
        try:
            chu = len((await api.messages.get_conversation_members(peer_id=2000000000 + i[0], group_id=GROUP_ID)).items)
        except:
            chu = 0
        msg += f'➖ {i[0]} | M: {i[1]} | C: {chu} | N: {await getChatName(i[0])} \n'
    await messagereply(message, msg)


@bl.chat_message(SearchCMD('getchats'))
async def getchats(message: Message):
    limit = message.text.split()[-1]
    async with (await pool()).acquire() as conn:
        top = await conn.fetch('select chat_id, messages from messages order by messages desc limit $1',
                               int(limit) if limit.isdigit() else 100)
    msg = '✝ Беседы:\n'
    for i in top:
        if str(i[0]) in msg or await getUInfBanned(0, i[0]):
            continue
        try:
            chu = len((await api.messages.get_conversation_members(peer_id=2000000000 + i[0], group_id=GROUP_ID)).items)
        except:
            chu = 0
        msg += f'➖ {i[0]} | M: {i[1]} | C: {chu} | N: {await getChatName(i[0])}\n'
    await messagereply(message, msg)


@bl.chat_message(SearchCMD('helpdev'))
async def helpdev(message: Message):
    await messagereply(message, messages.helpdev())


@bl.chat_message(SearchCMD('gettransferhistory'))
@bl.chat_message(SearchCMD('gettransferhistoryto'))
@bl.chat_message(SearchCMD('gettransferhistoryfrom'))
async def gettransferhistory(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        await messagereply(message, '🔶 Пользователь не найден')
        return
    limit = message.text.split()[-1]
    limit = int(limit) if limit.isdigit() else 100
    async with (await pool()).acquire() as conn:
        if message.text.lower().split()[0][-2:] == 'to':
            transfers = await conn.fetch(
                'select from_id, to_id, amount, com from transferhistory where to_id=$1 '
                'order by time desc limit $2', id, limit)
        elif message.text.lower().split()[0][-4:] == 'from':
            transfers = await conn.fetch(
                'select from_id, to_id, amount, com from transferhistory where from_id=$1 '
                'order by time desc limit $2', id, limit)
        else:
            transfers = await conn.fetch(
                'select from_id, to_id, amount, com from transferhistory where from_id=$1 or to_id=$1'
                ' order by time desc limit $2', id, limit)
    msg = '✝ Общие трансферы пользователя:'
    for i in transfers:
        msg += (f'\n F: [id{i[0]}|{await getUserName(i[0])}] | T: [id{i[1]}|{await getUserName(i[1])}] | A: {i[2]} | C:'
                f' {not bool(i[3])}')
    await messagereply(message, msg)


@bl.chat_message(SearchCMD('lvlban'))
async def lvlban(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await messagereply(message, messages.lvlban_hint())
    async with (await pool()).acquire() as conn:
        await conn.execute('insert into lvlbanned (uid) values ($1) on conflict (uid) do nothing', id)
    await messagereply(message, messages.lvlban())


@bl.chat_message(SearchCMD('lvlunban'))
async def lvlunban(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await messagereply(message, messages.lvlunban_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('delete from lvlbanned where uid=$1 returning 1', id):
            return await messagereply(message, messages.lvlunban_noban())
    await messagereply(message, messages.lvlunban())


@bl.chat_message(SearchCMD('lvlbanlist'))
async def lvlbanlist(message: Message):
    async with (await pool()).acquire() as conn:
        lvlban = await conn.fetch('select uid from lvlbanned')
    msg = f'⚛ Список пользователей в lvlban бота (Всего : {len(lvlban)})\n\n'
    for user in lvlban:
        msg += f"➖ {user[0]} : | [id{user[0]}|{await getUserName(user[0])}]\n"
    await messagereply(message, msg)


@bl.chat_message(SearchCMD('repban'))
async def repban(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await messagereply(message, messages.repban_hint())
    if not await getURepBanned(id):
        async with (await pool()).acquire() as conn:
            await conn.execute('insert into reportban (uid, time) values ($1, $2)', id, None)
    await messagereply(message, messages.repban())


@bl.chat_message(SearchCMD('repunban'))
async def repunban(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await messagereply(message, messages.repunban_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('delete from reportban where uid=$1 returning 1', id):
            return await messagereply(message, messages.repunban_noban())
    await messagereply(message, messages.repunban())


@bl.chat_message(SearchCMD('repbanlist'))
async def repbanlist(message: Message):
    async with (await pool()).acquire() as conn:
        repban = await conn.fetch('select uid from reportban')
    msg = f'⚛ Список пользователей в reportban бота (Всего : {len(repban)})\n\n'
    for user in repban:
        msg += f"➖ {user[0]} : | [id{user[0]}|{await getUserName(user[0])}]\n"
    await messagereply(message, msg)


@bl.chat_message(SearchCMD('chatsstats'))
async def chatsstats(message: Message):
    async with (await pool()).acquire() as conn:
        nm = await conn.fetchval('select count(*) as c from settings where setting=\'nightmode\' and pos=true')
        c = await conn.fetchval('select count(*) as c from settings where setting=\'captcha\' and pos=true')
    msg = (f'🌓 Ночной режим включен в: {pointWords(nm or 0, ["беседе", "беседах", "беседах"])}\n'
           f'🔢 Капча включена в: {pointWords(c or 0, ["беседе", "беседах", "беседах"])}')
    await messagereply(message, msg)


@bl.chat_message(SearchCMD('linked'))
async def linked(message: Message):
    async with (await pool()).acquire() as conn:
        c = await conn.fetchval('select count(*) as c from tglink where tgid IS NOT NULL')
    await messagereply(message, f'Связано с Telegram : {pointWords(c, ("аккаунт", "аккаунта", "аккаунтов"))}.')


@bl.chat_message(SearchCMD('cmdstats'))
async def cmdstats(message: Message):
    data = message.text.split()
    async with (await pool()).acquire() as conn:
        if len(data) == 2:
            c = await conn.fetch('select uid from cmdsusage where cmd=$1', data[1])
        else:
            c = await conn.fetch('select uid from cmdsusage')
    await messagereply(message, f'Использований: {pointWords(len(c), ("раз", "раза", "раз"))}.\n'
                                f'Уникальных использований: {pointWords(len(set(c)), ("раз", "раза", "раз"))}.')


@bl.chat_message(SearchCMD('promocreate'))
async def promocreate(message: Message):
    data = message.text.split()
    if len(data) not in (4, 5) or not data[2].isdigit():
        return await messagereply(message, messages.promocreate_hint())
    usage, date, xp = None, None, int(data[2])
    try:
        if data[3].isdigit():
            usage = int(data[3])
            date = datetime.strptime(data[4], '%d.%m.%Y') if len(data) > 4 else None
        else:
            date = datetime.strptime(data[3], '%d.%m.%Y')
    except ValueError:
        return await messagereply(message, messages.promocreate_hint())
    async with (await pool()).acquire() as conn:
        if await conn.fetchval('select exists(select 1 from promocodes where code=$1)', data[1]):
            return await messagereply(message, messages.promocreate_alreadyexists(data[1]))
        await conn.execute('insert into promocodes (code, usage, date, xp) values ($1, $2, $3, $4)',
                           data[1], usage, (date.timestamp() + 86399) if date else None, xp)
    await messagereply(message, messages.promocreate(data[1], xp, usage, date))


@bl.chat_message(SearchCMD('promodel'))
async def promodel(message: Message):
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(message, messages.promodel_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('delete from promocodes where code=$1 returning 1', data[1]):
            return await messagereply(message, messages.promodel_notfound(data[1]))
    await messagereply(message, messages.promodel(data[1]))


@bl.chat_message(SearchCMD('promolist'))
async def promolist(message: Message):
    async with (await pool()).acquire() as conn:
        promos = await conn.fetch('select code from promocodeuses where code=ANY($1)',
                                  [i[0] for i in await conn.fetch('select code from promocodes')])
    promos = [i[0] for i in promos]
    await messagereply(message, messages.promolist({k: promos.count(k) for k in set(promos)}))


@bl.chat_message(SearchCMD('allowinvite'))
async def allowinvite(message: Message):
    data = message.text.split()
    if len(data) != 2 or data[1] not in ('1', '2'):
        return await messagereply(message, messages.allowinvite_hint())
    if data[-1] == '1':
        async with (await pool()).acquire() as conn:
            await conn.execute(
                'insert into referralbonus (chat_id) values ($1) on conflict (chat_id) do nothing', message.chat_id)
        await messagereply(message, messages.allowinvite_on())
    else:
        async with (await pool()).acquire() as conn:
            await conn.execute('delete from referralbonus where chat_id=$1', message.chat_id)
        await messagereply(message, messages.allowinvite_off())


@bl.chat_message(SearchCMD('prempromocreate'))
async def prempromocreate(message: Message):
    data = message.text.split()
    if len(data) != 4 or not data[2].isdigit():
        return await messagereply(message, messages.prempromocreate_hint())
    try:
        date = datetime.strptime(data[3], '%d.%m.%Y')
    except ValueError:
        return await messagereply(message, messages.prempromocreate_hint())
    async with (await pool()).acquire() as conn:
        if await conn.fetchval('select exists(select 1 from prempromo where promo=$1)', data[1]):
            return await messagereply(message, messages.prempromocreate_alreadyexists(data[1]))
        await conn.execute('insert into prempromo (promo, val, start, "end", uid) values ($1, $2, $3, $4, null)',
                           data[1], int(data[2]), time.time(), (date.timestamp() + 86399))
    await messagereply(message, messages.prempromocreate(data[1], data[2], date))


@bl.chat_message(SearchCMD('prempromodel'))
async def prempromodel(message: Message):
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(message, messages.prempromodel_hint())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('delete from prempromo where promo=$1 returning 1', data[1]):
            return await messagereply(message, messages.prempromodel_notfound(data[1]))
    await messagereply(message, messages.prempromodel(data[1]))


@bl.chat_message(SearchCMD('prempromolist'))
async def prempromolist(message: Message):
    async with (await pool()).acquire() as conn:
        promos = await conn.fetch('select promo, "end" from prempromo')
    await messagereply(message, messages.prempromolist(promos))


@bl.chat_message(SearchCMD('bonuslist'))
async def bonuslist(message: Message):
    async with (await pool()).acquire() as conn:
        users = await conn.fetch('select uid, streak from bonus order by streak desc limit 50')
    await messagereply(message, '\n'.join([
        f'{k + 1}. [id{i[0]}|{await getUserName(i[0])}] - Серия: {pointWords(i[1] + 1, ("день", "дня", "дней"))}'
        for k, i in enumerate(users)]))
