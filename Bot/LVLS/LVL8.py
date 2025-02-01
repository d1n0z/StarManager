import asyncio
import importlib
import os
import statistics
import sys
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
    setUserAccessLevel, pointWords, chunks, getURepBanned, pointMinutes
from config.config import API, GROUP_ID, DEVS, PATH
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
    await message.reply('💚 Completed.')


@bl.chat_message(SearchCMD('botinfo'))
async def botinfo(message: Message):
    # completely broken(and bad), too lazy to fix
    await message.reply(disable_mentions=1, message='Эта команда отключена.')
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
    #     chat_users = await API.messages.get_conversation_members(i + 2000000000, group_id=GROUP_ID)
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
    # u_name = await API.users.get(user_ids=746110579)
    # biggest_gpool_owner_name = f"{u_name[0].first_name} {u_name[0].last_name}"
    # msg = messages.bot_info(chats, total_users, users, premium_users, all_groups, biggest_gpool,
    #                         biggest_gpool_owner_name, max_pool, max_group_name, max_group_count, biggest_chat_id,
    #                         biggest_chat_users, biggest_chat_owner_id, biggest_chat_owner_name)
    # await message.reply(msg)


@bl.chat_message(SearchCMD('msg'))
async def msg(message: Message):
    data = message.text.split()
    if len(data) <= 1:
        return await message.reply(messages.msg_hint())
    devmsg = ' '.join(data[1:])
    msg = messages.msg(devmsg)
    k = 0
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chats = await (await c.execute('select chat_id from allchats')).fetchall()
    for i in chunks(chats, 2500):
        try:
            k += len(i)
            code = ''
            for y in chunks(i, 100):
                code += ('API.messages.send({"random_id": 0, "peer_ids": [' + ','.join(str(o[0]) for o in y) +
                         '], "message": "' + f"{msg}" + '"});')
            await API.execute(code=code)
            print(f'sent {k}/{len(chats)}')
            await asyncio.sleep(1)
        except:
            pass
    msg = f'done {k}/{len(chats)}'
    print(msg)
    await message.reply(msg)


@bl.chat_message(SearchCMD('addblack'))
async def addblack(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        return await message.reply(messages.addblack_hint())
    if id == uid:
        return await message.reply(messages.addblack_myself())
    if id < 0:
        return await message.reply(messages.id_group())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into blacklist (uid) values (%s) on conflict (uid) do nothing', (id,))
            await conn.commit()
    dev_name = await getUserName(uid)
    dev_nickname = await getUserNickname(uid, chat_id)
    await message.reply(messages.addblack(uid, dev_name, dev_nickname, id, await getUserName(id),
                                          await getUserNickname(id, chat_id)))
    await sendMessage(id, messages.blacked(uid, dev_name, dev_nickname))


@bl.chat_message(SearchCMD('delblack'))
async def delblack(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        return await message.reply(messages.delblack_hint())
    if id == uid:
        return await message.reply(messages.delblack_myself())
    if id < 0:
        return await message.reply(messages.id_group())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from blacklist where uid=%s', (id,))).rowcount:
                return await message.reply(messages.delblack_no_user(
                    id, await getUserName(id), await getUserNickname(id, chat_id)))
            await conn.commit()
    dev_name = await getUserName(uid)
    dev_nickname = await getUserNickname(uid, chat_id)
    await message.reply(messages.delblack(uid, dev_name, dev_nickname, id, await getUserName(id),
                                          await getUserNickname(id, chat_id)))
    await sendMessage(id, messages.delblacked(uid, dev_name, dev_nickname))


@bl.chat_message(SearchCMD('blacklist'))
async def blacklist(message: Message):
    users = {}
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            blc = await (await c.execute('select uid from blacklist')).fetchall()
    for user in blc:
        users[await getUserName(user[0])] = user[0]
    msg = f'⚛ Список пользователей в ЧС бота (Всего : {len(list(users))})\n\n'
    for k, i in users.items():
        msg += f"➖ {i} : | [id{i}|{k}]\n"
    await message.reply(msg)


@bl.chat_message(SearchCMD('setstatus'))
async def setstatus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    data = message.text.split()
    if id == 0 or not data[2].isdigit():
        return await message.reply(messages.setstatus_hint())
    if id < 0:
        return await message.reply(messages.id_group())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update premium set time = %s where uid=%s',
                                    (int(time.time() + int(data[2]) * 86400), id))).rowcount:
                await c.execute('insert into premium (uid, time) values (%s, %s)',
                                (id, int(time.time() + int(data[2]) * 86400)))
            await conn.commit()

    dev_name = await getUserName(uid)
    await message.reply(messages.setstatus(uid, dev_name, await getUserNickname(uid, chat_id),
                                           id, await getUserName(id), await getUserNickname(id, chat_id)))
    await sendMessage(id, messages.ugiveStatus(data[2], uid, dev_name))


@bl.chat_message(SearchCMD('delstatus'))
async def delstatus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    data = message.text.split()
    if id == 0:
        return await message.reply(messages.delstatus_hint())
    if id < 0:
        return await message.reply(messages.id_group())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from premium where uid=%s', (id,))
            await conn.commit()

    dev_name = await getUserName(uid)
    await message.reply(messages.setstatus(uid, dev_name, await getUserNickname(uid, chat_id),
                                           id, await getUserName(id), await getUserNickname(id, chat_id)))
    await sendMessage(id, messages.ugiveStatus(data[2], uid, dev_name))


@bl.chat_message(SearchCMD('statuslist'))
async def statuslist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            prem = await (await c.execute('select uid, time from premium')).fetchall()
    await message.reply(await messages.statuslist(prem), keyboard=keyboard.statuslist(message.from_id, 0, len(prem)))


@bl.chat_message(SearchCMD('setprem'))
async def setprem(message: Message):
    uid = message.from_id
    chat_id = await getIDFromMessage(message.text, message.reply_message)
    if chat_id <= 0:
        return await message.reply(messages.setprem_hint())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update publicchats set premium = true where chat_id=%s', (chat_id,))).rowcount:
                await c.execute('insert into publicchats (chat_id, premium, isopen) values (%s, true, false)',
                                (chat_id,))
            await conn.commit()

    await message.reply(messages.setprem(chat_id))
    await sendMessage(message.peer_id, messages.premchat(uid, await getUserName(uid)))


@bl.chat_message(SearchCMD('delprem'))
async def delprem(message: Message):
    chat_id = await getIDFromMessage(message.text, message.reply_message)
    if chat_id <= 0:
        return await message.reply(messages.delprem_hint())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('update publicchats set premium = false where chat_id=%s', (chat_id,))
            await conn.commit()
    await message.reply(messages.delprem(chat_id))


@bl.chat_message(SearchCMD('premlist'))
async def permlist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            prem = await (await c.execute('select chat_id from publicchats where premium=true')).fetchall()
    await message.reply(messages.premlist(prem))


@bl.chat_message(SearchCMD('givexp'))
async def givexp(message: Message):
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply('🔶 Пользователь не найден')
    data = message.text.split()
    await addUserXP(id, int(data[2]))
    await message.reply(messages.givexp(uid, await getUserName(uid), id, await getUserName(id), data[2]))


@bl.chat_message(SearchCMD('resetlvl'))
async def resetlvl(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply('🔶 Пользователь не найден')
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('update xp set xp=0, lvl=0, league=1 where uid=%s', (id,))
            await conn.commit()
    u_name = await getUserName(id)
    msgsent = messages.resetlvlcomplete(id, u_name)
    try:
        await API.messages.send(random_id=0, user_id=id, message=messages.resetlvl(id, u_name))
    except:
        msgsent += '\n❗ Пользователю не удалось отправить сообщение'
    await message.reply(msgsent)


@bl.chat_message(SearchCMD('infban'))
async def infban(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if len(data) != 3 or data[1] not in ['group', 'user'] or not id:
        return await message.reply(messages.infban_hint())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute(
                'insert into infbanned (uid, type) values (%s, %s) on conflict (uid) do nothing', (id, data[1]))
            await conn.commit()
    await message.reply(messages.infban())


@bl.chat_message(SearchCMD('infunban'))
async def infunban(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if len(data) != 3 or data[1] not in ['group', 'user'] or not id:
        return await message.reply(messages.infunban_hint())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from infbanned where uid=%s and type=%s', (id, data[1]))).rowcount:
                return await message.reply(messages.infunban_noban())
            await conn.commit()
    await message.reply(messages.infunban())


@bl.chat_message(SearchCMD('inflist'))
async def inflist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            inf = await (await c.execute('select type, uid from infbanned')).fetchall()
    msg = f'⚛ Список пользователей и бесед в inf бота (Всего : {len(inf)})\n\n'
    for user in inf:
        if user[0] == 'user':
            name = await getUserName(user[1])
            msg += f"➖ user {user[1]} : | {name}\n"
        else:
            name = await getChatName(user[1])
            msg += f"➖ chat {user[1]} : | {name}\n"
    await message.reply(msg)


@bl.chat_message(SearchCMD('cmdcount'))
async def cmdcount(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cmdsraw = await (await c.execute(
                'select cmd, timestart, timeend from commandsstatistics where timeend is not null')).fetchall()
    cmds = {}
    for i in cmdsraw:
        if i[0] not in cmds:
            cmds[i[0]] = [i[2].timestamp() - i[1].timestamp()]
        else:
            cmds[i[0]].append(i[2].timestamp() - i[1].timestamp())
    msg = ''
    for i in cmds.keys():
        msg += f'{i}: {statistics.mean(cmds[i])} секунд | использован {len(cmds[i])} раз\n'
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('msgsaverage'))
async def cmdcount(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            msts = await (await c.execute(
                'select timestart, timeend from messagesstatistics where timeend is not null')).fetchall()
    msgs = [i[1].timestamp() - i[0].timestamp() for i in msts]
    await message.reply(disable_mentions=1, message=f'Среднее время обработки - {statistics.mean(msgs)} секунд')


@bl.chat_message(SearchCMD('msgscount'))
async def cmdcount(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            msgs5minutes = await (await c.execute(
                'select count(*) as c from messagesstatistics where timeend is not null and '
                'extract(minute from timestart)>=%s and extract(hour from timestart)=%s and '
                'extract(day from timestart)=%s and extract(month from timestart)=%s and '
                'extract(year from timestart)=%s', (datetime.now().minute - 5, datetime.now().hour, datetime.now().day,
                                                    datetime.now().month, datetime.now().year))).fetchone()
            msgsminute = await (await c.execute(
                'select count(*) as c from messagesstatistics where timeend is not null and '
                'extract(minute from timestart)=%s and extract(hour from timestart)=%s and '
                'extract(day from timestart)=%s and extract(month from timestart)=%s and '
                'extract(year from timestart)=%s', (datetime.now().minute, datetime.now().hour, datetime.now().day,
                                                    datetime.now().month, datetime.now().year))).fetchone()
            msgshour = await (await c.execute(
                'select count(*) as c from messagesstatistics where timeend is not null and '
                'extract(hour from timestart)=%s and extract(day from timestart)=%s and '
                'extract(month from timestart)=%s and extract(year from timestart)=%s',
                (datetime.now().hour, datetime.now().day, datetime.now().month, datetime.now().year))).fetchone()
            msgslasthour = await (await c.execute(
                'select count(*) as c from messagesstatistics where timeend is not null and '
                'extract(hour from timestart)=%s and extract(day from timestart)=%s and '
                'extract(month from timestart)=%s and extract(year from timestart)=%s',
                (datetime.now().hour - 1, datetime.now().day, datetime.now().month, datetime.now().year))).fetchone()
            msgsday = await (await c.execute(
                'select count(*) as c from messagesstatistics where timeend is not null and '
                'extract(day from timestart)=%s and extract(month from timestart)=%s and '
                'extract(year from timestart)=%s',
                (datetime.now().day,  datetime.now().month, datetime.now().year))).fetchone()
            msgslastday = await (await c.execute(
                'select count(*) as c from messagesstatistics where timeend is not null and '
                'extract(day from timestart)=%s and extract(month from timestart)=%s and '
                'extract(year from timestart)=%s',
                (datetime.now().day - 1,  datetime.now().month, datetime.now().year))).fetchone()
    await message.reply(disable_mentions=1, message=f'{msgslastday[0]} сообщений за вчера\n'
                                                    f'{msgslasthour[0]} сообщений за прошлый час\n'
                                                    f'{msgs5minutes[0]} сообщений за последние 5 минут\n'
                                                    f'{msgsday[0]} сообщений за сегодня\n'
                                                    f'{msgshour[0]} сообщений за этот час\n'
                                                    f'{msgsminute[0]} сообщений за эту минуту')


@bl.chat_message(SearchCMD('mwaverage'))
async def cmdcount(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            mwst = await (await c.execute(
                'select timestart, timeend from middlewaresstatistics where timeend is not null')).fetchall()
    average = statistics.mean([i[1].timestamp() - i[0].timestamp() for i in mwst])
    await message.reply(disable_mentions=1, message=f'Среднее время работы мидлвари - {average} секунд')


@bl.chat_message(SearchCMD('getlink'))
async def getlink(message: Message):
    data = message.text.lower().split()
    if len(data) != 2 or not data[1].isdigit():
        return await message.reply('/getlink chat_id')
    try:
        await message.reply(
            (await API.messages.get_invite_link(peer_id=int(data[1]) + 2000000000, reset=0, group_id=GROUP_ID)).link)
    except:
        await message.reply('❌ Невозможно сгенерировать ссылку')


@bl.chat_message(SearchCMD('reboot'))
async def reboot(message: Message):
    if len(data := message.text.split()) == 2:
        await message.reply(
            f'⌛ Перезагрузка произойдет через {pointWords(int(data[1]), ("минуту", "минуты", "минут"))}.')
        await asyncio.sleep(int(data[1]) * 60)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into reboots (chat_id, time, sended) values (%s, %s, false)',
                            (message.chat_id, int(time.time())))
            await conn.commit()
    await message.reply(messages.reboot())
    os.system(PATH + 'startup.sh')  # noqa


@bl.chat_message(SearchCMD('sudo'))
async def sudo(message: Message):
    if 'reboot' in message.text:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('insert into reboots (chat_id, time, sended) values (%s, %s, false)',
                                (message.chat_id, int(time.time())))
                await conn.commit()
    await message.reply(os.popen(f'sudo {" ".join(message.text.split()[1:])}').read())


@bl.chat_message(SearchCMD('getuserchats'))
async def getuserchats(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply('🔶 Пользователь не найден')
    limit = message.text.split()[-1]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            top = await (await c.execute(
                'select chat_id, messages from messages where uid=%s order by messages desc limit %s',
                (id, int(limit) if limit.isdigit() else 100))).fetchall()
    msg = '✝ Беседы пользователя:\n'
    for i in top:
        if await getUInfBanned(id, i[0]):
            continue
        try:
            chu = len((await API.messages.get_conversation_members(peer_id=2000000000 + i[0], group_id=GROUP_ID)).items)
        except:
            chu = 0
        msg += f'➖ {i[0]} | M: {i[1]} | C: {chu} | N: {await getChatName(i[0])} \n'
    await message.reply(msg)


@bl.chat_message(SearchCMD('getchats'))
async def getchats(message: Message):
    limit = message.text.split()[-1]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            top = await (await c.execute('select chat_id, messages from messages order by messages desc limit %s',
                                         (int(limit) if limit.isdigit() else 100,))).fetchall()
    msg = '✝ Беседы:\n'
    for i in top:
        if str(i[0]) in msg or await getUInfBanned(0, i[0]):
            continue
        try:
            chu = len((await API.messages.get_conversation_members(peer_id=2000000000 + i[0], group_id=GROUP_ID)).items)
        except:
            chu = 0
        msg += f'➖ {i[0]} | M: {i[1]} | C: {chu} | N: {await getChatName(i[0])}\n'
    await message.reply(msg)


@bl.chat_message(SearchCMD('helpdev'))
async def helpdev(message: Message):
    await message.reply(messages.helpdev())


@bl.chat_message(SearchCMD('gettransferhistory'))
@bl.chat_message(SearchCMD('gettransferhistoryto'))
@bl.chat_message(SearchCMD('gettransferhistoryfrom'))
async def gettransferhistory(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        await message.reply('🔶 Пользователь не найден')
        return
    limit = message.text.split()[-1]
    limit = int(limit) if limit.isdigit() else 100
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if message.text.lower().split()[0][-2:] == 'to':
                transfers = await (await c.execute(
                    'select from_id, to_id, amount, com from transferhistory where to_id=%s '
                    'order by time desc limit %s', (id, limit))).fetchall()
            elif message.text.lower().split()[0][-4:] == 'from':
                transfers = await (await c.execute(
                    'select from_id, to_id, amount, com from transferhistory where from_id=%s '
                    'order by time desc limit %s', (id, limit))).fetchall()
            else:
                transfers = await (await c.execute(
                    'select from_id, to_id, amount, com from transferhistory where from_id=%s or to_id=%s'
                    ' order by time desc limit %s', (id, id, limit))).fetchall()
    msg = '✝ Общие трансферы пользователя:'
    for i in transfers:
        msg += (f'\n F: [id{i[0]}|{await getUserName(i[0])}] | T: [id{i[1]}|{await getUserName(i[1])}] | A: {i[2]} | C:'
                f' {not bool(i[3])}')
    await message.reply(msg)


@bl.chat_message(SearchCMD('lvlban'))
async def lvlban(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await message.reply(messages.lvlban_hint())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into lvlbanned (uid) values (%s) on conflict (uid) do nothing', (id,))
            await conn.commit()
    await message.reply(messages.lvlban())


@bl.chat_message(SearchCMD('lvlunban'))
async def lvlunban(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await message.reply(messages.lvlunban_hint())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from lvlbanned where uid=%s', (id,))).rowcount:
                return await message.reply(messages.lvlunban_noban())
            await conn.commit()
    await message.reply(messages.lvlunban())


@bl.chat_message(SearchCMD('lvlbanlist'))
async def lvlbanlist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lvlban = await (await c.execute('select uid from lvlbanned')).fetchall()
    msg = f'⚛ Список пользователей в lvlban бота (Всего : {len(lvlban)})\n\n'
    for user in lvlban:
        msg += f"➖ {user[0]} : | [id{user[0]}|{await getUserName(user[0])}]\n"
    await message.reply(msg)


@bl.chat_message(SearchCMD('repban'))
async def repban(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await message.reply(messages.repban_hint())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not await getURepBanned(id):
                await c.execute('insert into reportban (uid) values (%s)', (id,))
            await conn.commit()
    await message.reply(messages.repban())


@bl.chat_message(SearchCMD('repunban'))
async def repunban(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        return await message.reply(messages.repunban_hint())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from reportban where uid=%s', (id,))).rowcount:
                msg = messages.repunban_noban()
                await message.reply(msg)
                return
            await conn.commit()
    await message.reply(messages.repunban())


@bl.chat_message(SearchCMD('repbanlist'))
async def repbanlist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            repban = await (await c.execute('select uid from reportban')).fetchall()
    msg = f'⚛ Список пользователей в reportban бота (Всего : {len(repban)})\n\n'
    for user in repban:
        msg += f"➖ {user[0]} : | [id{user[0]}|{await getUserName(user[0])}]\n"
    await message.reply(msg)


@bl.chat_message(SearchCMD('chatsstats'))
async def chatsstats(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            nm = (await (await c.execute(
                'select count(*) as c from settings where setting=\'nightmode\' and pos=true')).fetchone())[0]
            c = (await (await c.execute(
                'select count(*) as c from settings where setting=\'captcha\' and pos=true')).fetchone())[0]
    msg = (f'🌓 Ночной режим включен в: {pointWords(nm, ["беседе", "беседах", "беседах"])}\n'
           f'🔢 Капча включена в: {pointWords(c, ["беседе", "беседах", "беседах"])}')
    await message.reply(msg)


@bl.chat_message(SearchCMD('linked'))
async def linked(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            c = (await (await c.execute(
                'select count(*) as c from tglink where tgid IS NOT NULL')).fetchone())[0]
    await message.reply(f'Связано с Telegram : {pointWords(c, ("аккаунт", "аккаунта", "аккаунтов"))}.')
