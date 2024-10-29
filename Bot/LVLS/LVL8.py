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
    setUserAccessLevel, pointWords, chunks
from config.config import API, GROUP_ID, DEVS
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('getdev'))
async def getdev_handler(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if uid in DEVS:
        await setUserAccessLevel(uid, chat_id, 8)


@bl.chat_message(SearchCMD('backup'))
async def backup_handler(message: Message):
    await backup()
    await message.reply('💚 Completed.')


@bl.chat_message(SearchCMD('botinfo'))
async def botinfo(message: Message):
    # completely broken
    await message.reply(disable_mentions=1, message='Эта команда отключена.')  # chat_id = message.peer_id - 2000000000
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
        msg = messages.msg_hint()
        await message.reply(msg)
        return
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
    print(f'done {k}/{len(chats)}')


@bl.chat_message(SearchCMD('addblack'))
async def addblack(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        msg = messages.addblack_hint()
        await message.reply(msg)
        return
    if id == uid:
        msg = messages.addblack_myself()
        await message.reply(msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(msg)
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into blacklist (uid) values (%s) on conflict (uid) do nothing', (id,))
            await conn.commit()
    dev_name = await getUserName(uid)
    u_name = await getUserName(id)
    u_nickname = await getUserNickname(uid, chat_id)
    nickname = await getUserNickname(id, chat_id)
    msg = messages.addblack(uid, dev_name, u_nickname, id, u_name, nickname)
    await message.reply(msg)
    msg = messages.blacked(uid, dev_name, u_nickname)
    await sendMessage(id, msg)


@bl.chat_message(SearchCMD('delblack'))
async def delblack(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == 0:
        msg = messages.delblack_hint()
        await message.reply(msg)
        return
    if id == uid:
        msg = messages.delblack_myself()
        await message.reply(msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(msg)
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from blacklist where uid=%s', (id,))).rowcount:
                u_name = await getUserName(id)
                nick = await getUserNickname(id, chat_id)
                msg = messages.delblack_no_user(id, u_name, nick)
                await message.reply(msg)
                return
            await conn.commit()
    dev_name = await getUserName(uid)
    u_name = await getUserName(id)
    u_nickname = await getUserNickname(uid, chat_id)
    nick = await getUserNickname(id, chat_id)
    msg = messages.delblack(uid, dev_name, u_nickname, id, u_name, nick)
    await message.reply(msg)
    msg = messages.delblacked(uid, dev_name, u_nickname)
    await sendMessage(id, msg)


@bl.chat_message(SearchCMD('blacklist'))
async def blacklist(message: Message):
    users = {}
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            blc = await (await c.execute('select uid from blacklist')).fetchall()
    for user in blc:
        name = await getUserName(user[0])
        if name.count('DELETED') == 0:
            users[name] = user[0]

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
        msg = messages.setstatus_hint()
        await message.reply(msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(msg)
        return
    dev_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    u_name = await getUserName(id)
    nick = await getUserNickname(id, chat_id)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update premium set time = %s where uid=%s',
                                    (int(time.time() + int(data[2]) * 86400), id))).rowcount:
                await c.execute('insert into premium (uid, time) values (%s, %s)',
                                (id, int(time.time() + int(data[2]) * 86400)))
            await conn.commit()

    msg = messages.setstatus(uid, dev_name, u_nickname, id, u_name, nick)
    await message.reply(msg)
    msg = messages.ugiveStatus(data[2], uid, dev_name)
    await sendMessage(id, msg)


@bl.chat_message(SearchCMD('givexp'))
async def givexp(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if id is None:
        return
    uid = message.from_id
    dev_name = await API.users.get(user_ids=uid)
    dev_name = f"{dev_name[0].first_name} {dev_name[0].last_name}"
    u_name = await API.users.get(user_ids=id)
    u_name = f"{u_name[0].first_name} {u_name[0].last_name}"
    data = message.text.split()
    await addUserXP(id, int(data[2]))
    msg = messages.givexp(uid, dev_name, id, u_name, int(data[2]))
    await message.reply(msg)


@bl.chat_message(SearchCMD('resetlvl'))
async def resetlvl(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if id is None:
        await message.reply('🔶 Пользователь не найден')
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('update xp set xp=0 where uid=%s', (id,))
            await c.execute('update coins set coins=0 where uid=%s', (id,))
            await conn.commit()
    u_name = await getUserName(id)
    msg = messages.resetlvl(id, u_name)
    msgsent = messages.resetlvlcomplete(id, u_name)
    try:
        await API.messages.send(random_id=0, user_id=id, message=msg)
    except:
        msgsent += '\n❗ Пользователю не удалось отправить сообщение'
    await message.reply(msgsent)


@bl.chat_message(SearchCMD('delstatus'))
async def delstatus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    data = message.text.split()
    if id == 0:
        msg = messages.delstatus_hint()
        await message.reply(msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(msg)
        return
    dev_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    u_name = await getUserName(id)
    nick = await getUserNickname(id, chat_id)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from premium where uid=%s', (id,))
            await conn.commit()

    msg = messages.setstatus(uid, dev_name, u_nickname, id, u_name, nick)
    await message.reply(msg)
    msg = messages.ugiveStatus(data[2], uid, dev_name)
    await sendMessage(id, msg)


@bl.chat_message(SearchCMD('statuslist'))
async def statuslist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            prem = await (await c.execute('select uid, time from premium').fetchall())
    premium_uids = [i[0] for i in prem]
    names = await API.users.get(user_ids=','.join([f'{i}' for i in premium_uids]))
    msg = messages.statuslist(names, prem)
    kb = keyboard.statuslist(message.from_id, 0, len(names))
    await message.reply(msg, keyboard=kb)


@bl.chat_message(SearchCMD('infban'))
async def infban(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if len(data) != 3 or data[1] not in ['group', 'user'] or not id:
        msg = messages.infban_hint()
        await message.reply(msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute(
                'insert into infbanned (uid, type) values (%s, %s) on conflict (uid) do nothing', (id, data[1]))
            await conn.commit()

    msg = messages.infban()
    await message.reply(msg)


@bl.chat_message(SearchCMD('infunban'))
async def infunban(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if len(data) != 3 or data[1] not in ['group', 'user'] or not id:
        msg = messages.infunban_hint()
        await message.reply(msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from infbanned where uid=%s and type=%s', (id, data[1]))).rowcount:
                msg = messages.infunban_noban()
                await message.reply(msg)
                return
            await conn.commit()

    msg = messages.infunban()
    await message.reply(msg)


@bl.chat_message(SearchCMD('inflist'))
async def inflist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            inf = await (await c.execute('select type, uid from infbanned')).fetchall()
    msg = f'⚛ Список пользователей в inf бота (Всего : {len(inf)})\n\n'
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
    await message.reply(disable_mentions=1, message=f'{msgslastday[0]} сообщений в за вчера\n'
                                                    f'{msgslasthour[0]} сообщений за прошлый час\n'
                                                    f'{msgs5minutes[0]} сообщений за последние 5 минут\n'
                                                    f'{msgsday[0]} сообщений в за сегодня\n'
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
        await message.reply('/getlink chat_id')
        return
    try:
        invitelink = await API.messages.get_invite_link(peer_id=int(data[1]) + 2000000000, reset=0, group_id=GROUP_ID)
        await message.reply(invitelink.link)
    except:
        traceback.print_exc()
        await message.reply('❌ Невозможно сгенерировать ссылку')


@bl.chat_message(SearchCMD('reportwarn'))
async def reportwarn(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if id is not None:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                uwarns = await (await c.execute('select warns from reportwarns where uid=%s', (id,))).fetchone()
        uwarns = uwarns[0] if uwarns else 0
        kb = keyboard.warn_report(id, uwarns)
        msg = messages.reportwarn(id, await getUserName(id), uwarns)
        await message.reply(msg, keyboard=kb)


@bl.chat_message(SearchCMD('reboot'))
async def reboot(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into reboots (chat_id, time, sended) values (%s, %s, false)',
                            (message.chat_id, int(time.time())))
            await conn.commit()
    msg = messages.reboot()
    await message.reply(msg)
    os.system('/root/startup.sh')


@bl.chat_message(SearchCMD('sudo'))
async def sudo(message: Message):
    if 'reboot' in message.text:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('insert into reboots (chat_id, time, sended) values (%s, %s, false)',
                                (message.chat_id, int(time.time())))
                await conn.commit()
    await message.reply(os.popen(f'sudo {" ".join(message.text.split()[1:])}').read())


@bl.chat_message(SearchCMD('reimport'))
async def reimport(message: Message):
    # tbh useless shit
    await message.reply("♿ Реимпорт библиотек...")
    modules = sys.modules.values()
    for module in [i for i in modules][::-1]:
        if (hasattr(module, '__spec__') and
                hasattr(module.__spec__, 'origin') and
                isinstance(module.__spec__.origin, str) and
                'root/StarManager/' in module.__spec__.origin and
                'root/StarManager/venv' not in module.__spec__.origin):
            importlib.reload(module)
    await message.reply("✝ Библиотеки реимпортированы")


@bl.chat_message(SearchCMD('getuserchats'))
async def getuserchats(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if id is None:
        await message.reply('🔶 Пользователь не найден')
        return
    limit = message.text.split()[-1]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            top = await (await c.execute(
                'select chat_id, messages from messages where uid=%s order by messages desc limit %s',
                (id, int(limit) if limit.isdigit() else 100))).fetchall()
    msg = '✝ Беседы пользователя:\n'
    # edit = await message.reply(msg)
    for i in top:
        if await getUInfBanned(id, i[0]):
            continue
        try:
            chu = (await API.messages.get_conversation_members(peer_id=2000000000 + i[0], group_id=GROUP_ID)).items
        except:
            chu = []
        msg += f'➖ {i[0]} | M: {i[1]} | C: {len(chu)} | N: {await getChatName(i[0])} \n'
        # await API.messages.edit(edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)
    await message.reply(msg)


@bl.chat_message(SearchCMD('getchats'))
async def getchats(message: Message):
    limit = message.text.split()[-1]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            top = await (await c.execute('select chat_id, messages from messages order by messages desc limit %s',
                                         (int(limit) if limit.isdigit() else 100,))).fetchall()
    msg = '✝ Беседы:\n'
    # edit = await message.reply(msg)
    b = []
    for i in top:
        if i[0] in b or await getUInfBanned(0, i[0]):
            continue
        b.append(i[0])
        try:
            chu = (await API.messages.get_conversation_members(peer_id=2000000000 + i[0], group_id=GROUP_ID)).items
        except:
            chu = []
        msg += f'➖ {i[0]} | M: {i[1]} | C: {len(chu)} | N: {await getChatName(i[0])}\n'
        # await API.messages.edit(edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)
    await message.reply(msg)


@bl.chat_message(SearchCMD('helpdev'))
async def helpdev(message: Message):
    msg = messages.helpdev()
    await message.reply(msg)


@bl.chat_message(SearchCMD('gettransferhistory'))
@bl.chat_message(SearchCMD('gettransferhistoryto'))
@bl.chat_message(SearchCMD('gettransferhistoryfrom'))
async def gettransferhistory(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if id is None:
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
    # edit = await message.reply(msg)
    for i in transfers:
        from_n = await getUserName(i[0])
        to_n = await getUserName(i[1])
        msg += f'\n F: [id{i[0]}|{from_n}] | T: [id{i[1]}|{to_n}] | A: {i[2]} | C: {not bool(i[3])}'
        # await API.messages.edit(edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)
    await message.reply(msg)


@bl.chat_message(SearchCMD('lvlban'))
async def lvlban(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        msg = messages.lvlban_hint()
        await message.reply(msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into lvlbanned (uid) values (%s) on conflict (uid) do nothing', (id,))
            await conn.commit()

    msg = messages.lvlban()
    await message.reply(msg)


@bl.chat_message(SearchCMD('lvlunban'))
async def infunban(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if len(data) != 2 or not id:
        msg = messages.lvlunban_hint()
        await message.reply(msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from lvlbanned where uid=%s', (id,))).rowcount:
                msg = messages.lvlunban_noban()
                await message.reply(msg)
                return
            await conn.commit()

    msg = messages.lvlunban()
    await message.reply(msg)


@bl.chat_message(SearchCMD('lvlbanlist'))
async def lvlbanlist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lvlban = await (await c.execute('select uid from lvlbanned')).fetchall()
    msg = f'⚛ Список пользователей в lvlban бота (Всего : {len(lvlban)})\n\n'
    for user in lvlban:
        name = await getUserName(user[0])
        msg += f"➖ {user[0]} : | [id{user[0]}|{name}]\n"
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
