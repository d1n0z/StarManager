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
from Bot.checkers import getUInfBanned, checkCMD
from Bot.rules import SearchCMD
from Bot.utils import getUserName, getIDFromMessage, getUserNickname, sendMessage, addUserXP, getChatName, \
    setUserAccessLevel
from config.config import API, GROUP_ID, DEVS
from db import AllChats, Blacklist, Premium, InfBanned, ReportWarns, Reboot, XP, Coins, Messages, TransferHistory, \
    LvlBanned, CommandsStatistics, MessagesStatistics, MiddlewaresStatistics

bl = BotLabeler()


@bl.chat_message(SearchCMD('getdev'))
async def getdev_handler(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if await checkCMD(message, chat_id):
        if uid in DEVS:
            await setUserAccessLevel(uid, chat_id, 8)


@bl.chat_message(SearchCMD('backup'))
async def backup_handler(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if await checkCMD(message, chat_id):
        if uid in DEVS:
            from Bot.scheduler import backup
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(backup(), loop)


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
    chats = AllChats.select()
    for k, i in enumerate(chats):
        try:
            await API.messages.send(random_id=0, peer_ids=i.chat_id, message=msg)
            if k % 10 == 0:
                print(f'sent {k}/{len(chats)}')
        except:
            k -= 1
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
    Blacklist.get_or_create(uid=id)
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
    bl = Blacklist.get_or_none(Blacklist.uid == id)
    if bl is None:
        u_name = await getUserName(id)
        nick = await getUserNickname(id, chat_id)
        msg = messages.delblack_no_user(id, u_name, nick)
        await message.reply(msg)
        return
    bl.delete_instance()
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
    for user in Blacklist.select().iterator():
        name = await getUserName(user.uid)
        if name.count('DELETED') == 0:
            users[name] = user.uid

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

    pr = Premium.get_or_create(uid=id)[0]
    pr.time = time.time() + (int(data[2]) * 86400)
    pr.save()

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
    x = XP.get_or_none(XP.uid == id)
    if x is not None:
        x.xp = 0
        x.save()
    x = Coins.get_or_none(Coins.uid == id)
    if x is not None:
        x.count = 0
        x.save()
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

    pr = Premium.get_or_none(Premium.uid == id)
    if pr is not None:
        pr.delete_instance()

    msg = messages.setstatus(uid, dev_name, u_nickname, id, u_name, nick)
    await message.reply(msg)
    msg = messages.ugiveStatus(data[2], uid, dev_name)
    await sendMessage(id, msg)


@bl.chat_message(SearchCMD('statuslist'))
async def statuslist(message: Message):
    prem = Premium.select()
    premium_uids = [i.uid for i in prem]
    names = await API.users.get(user_ids=','.join([f'{i}' for i in premium_uids]))
    msg = messages.statuslist(names, prem)
    kb = keyboard.statuslist(message.from_id, 0)
    await message.reply(msg, keyboard=kb)


@bl.chat_message(SearchCMD('infban'))
async def infban(message: Message):
    data = message.text.lower().split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if len(data) != 3 or data[1] not in ['group', 'user'] or not id:
        msg = messages.infban_hint()
        await message.reply(msg)
        return

    InfBanned.get_or_create(uid=id, type=data[1])

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

    ib = InfBanned.get_or_none(InfBanned.uid == id, InfBanned.type == data[1])
    if ib is None:
        msg = messages.infunban_noban()
        await message.reply(msg)
        return
    ib.delete_instance()

    msg = messages.infunban()
    await message.reply(msg)


@bl.chat_message(SearchCMD('inflist'))
async def inflist(message: Message):
    infarr = InfBanned.select()
    msg = f'⚛ Список пользователей в inf бота (Всего : {len(infarr)})\n\n'
    for user in infarr:
        if user.type == 'user':
            name = await getUserName(user.uid)
            msg += f"➖ user {user.uid} : | {name}\n"
        else:
            name = await getChatName(user.uid)
            msg += f"➖ chat {user.uid} : | {name}\n"
    await message.reply(msg)


@bl.chat_message(SearchCMD('cmdcount'))
async def cmdcount(message: Message):
    cmdsraw = CommandsStatistics.select().where(CommandsStatistics.timeend.is_null(False))
    cmds = {}
    for i in cmdsraw.iterator():
        i: CommandsStatistics
        if i.cmd not in cmds:
            cmds[i.cmd] = [i.timeend.timestamp() - i.timestart.timestamp()]
        else:
            cmds[i.cmd].append(i.timeend.timestamp() - i.timestart.timestamp())
    msg = ''
    for i in cmds.keys():
        msg += f'{i}: {statistics.mean(cmds[i])} секунд | использован {len(cmds[i])} раз\n'
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('msgsaverage'))
async def cmdcount(message: Message):
    msgs = [i.timeend.timestamp() - i.timestart.timestamp() for i in
            MessagesStatistics.select().where(MessagesStatistics.timeend.is_null(False))]
    await message.reply(disable_mentions=1, message=f'Среднее время обработки - {statistics.mean(msgs)} секунд')


@bl.chat_message(SearchCMD('msgscount'))
async def cmdcount(message: Message):
    msgs5minutes = MessagesStatistics.select().where(MessagesStatistics.timeend.is_null(False),
                                                     MessagesStatistics.timestart.minute >= datetime.now().minute - 5,
                                                     MessagesStatistics.timestart.hour == datetime.now().hour,
                                                     MessagesStatistics.timestart.day == datetime.now().day,
                                                     MessagesStatistics.timestart.month == datetime.now().month,
                                                     MessagesStatistics.timestart.year == datetime.now().year).count()
    msgsminute = MessagesStatistics.select().where(MessagesStatistics.timeend.is_null(False),
                                                   MessagesStatistics.timestart.minute == datetime.now().minute,
                                                   MessagesStatistics.timestart.hour == datetime.now().hour,
                                                   MessagesStatistics.timestart.day == datetime.now().day,
                                                   MessagesStatistics.timestart.month == datetime.now().month,
                                                   MessagesStatistics.timestart.year == datetime.now().year).count()
    msgshour = MessagesStatistics.select().where(MessagesStatistics.timeend.is_null(False),
                                                 MessagesStatistics.timestart.hour == datetime.now().hour,
                                                 MessagesStatistics.timestart.day == datetime.now().day,
                                                 MessagesStatistics.timestart.month == datetime.now().month,
                                                 MessagesStatistics.timestart.year == datetime.now().year).count()
    msgslasthour = MessagesStatistics.select().where(MessagesStatistics.timeend.is_null(False),
                                                     MessagesStatistics.timestart.hour == datetime.now().hour - 1,
                                                     MessagesStatistics.timestart.day == datetime.now().day,
                                                     MessagesStatistics.timestart.month == datetime.now().month,
                                                     MessagesStatistics.timestart.year == datetime.now().year).count()
    msgsday = MessagesStatistics.select().where(MessagesStatistics.timeend.is_null(False),
                                                MessagesStatistics.timestart.day == datetime.now().day,
                                                MessagesStatistics.timestart.month == datetime.now().month,
                                                MessagesStatistics.timestart.year == datetime.now().year).count()
    await message.reply(disable_mentions=1, message=f'{msgsday} сообщений в за сегодня\n'
                                                    f'{msgslasthour} сообщений за прошлый час\n'
                                                    f'{msgshour} сообщений за этот час\n'
                                                    f'{msgs5minutes} сообщений за последние 5 минут\n'
                                                    f'{msgsminute} сообщений за эту минуту')


@bl.chat_message(SearchCMD('mwaverage'))
async def cmdcount(message: Message):
    average = statistics.mean([i.timeend.timestamp() - i.timestart.timestamp() for i in
                               MiddlewaresStatistics.select().where(MiddlewaresStatistics.timeend.is_null(False))])
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
        uwarns = ReportWarns.get_or_none(ReportWarns.uid == id)
        if uwarns is not None:
            uwarns = uwarns.warns
        else:
            uwarns = 0
        kb = keyboard.warn_report(id, uwarns)
        msg = messages.reportwarn(id, await getUserName(id), uwarns)
        await message.reply(msg, keyboard=kb)


@bl.chat_message(SearchCMD('reboot'))
async def reboot(message: Message):
    Reboot.create(chat_id=message.chat_id, time=time.time(), sended=0)
    msg = messages.reboot()
    await message.reply(msg)
    os.system('/root/startup.sh')


@bl.chat_message(SearchCMD('sudo'))
async def sudo(message: Message):
    if 'sudo reboot' in message.text:
        Reboot.create(chat_id=message.chat_id, time=time.time(), sended=0)
    await message.reply(os.popen(f'sudo {" ".join(message.text.split()[1:])}').read())


@bl.chat_message(SearchCMD('reimport'))
async def reimport(message: Message):
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
    top = (Messages.select().where(Messages.uid == id).
           order_by(Messages.messages.desc()).limit(int(limit) if limit.isdigit() else 100))
    msg = '✝ Беседы пользователя:\n'
    # edit = await message.reply(msg)
    for i in top:
        if not await getUInfBanned(id, i.chat_id):
            continue
        try:
            chu = (await API.messages.get_conversation_members(peer_id=2000000000 + i.chat_id, group_id=GROUP_ID)).items
        except:
            chu = []
        msg += f'➖ {i.chat_id} | M: {i.messages} | C: {len(chu)} | N: {await getChatName(i.chat_id)} \n'
        # await API.messages.edit(edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)
    await message.reply(msg)


@bl.chat_message(SearchCMD('getchats'))
async def getchats(message: Message):
    limit = message.text.split()[-1]
    top = Messages.select().order_by(Messages.messages.desc()).limit(int(limit) if limit.isdigit() else 100)
    msg = '✝ Беседы:\n'
    # edit = await message.reply(msg)
    b = []
    for i in top:
        if i.chat_id in b or not await getUInfBanned(0, i.chat_id):
            continue
        b.append(i.chat_id)
        try:
            chu = (await API.messages.get_conversation_members(peer_id=2000000000 + i.chat_id, group_id=GROUP_ID)).items
        except:
            chu = []
        msg += f'➖ {i.chat_id} | M: {i.messages} | C: {len(chu)} | N: {await getChatName(i.chat_id)}\n'
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
    if message.text.lower().split()[0][-2:] == 'to':
        transfers = (TransferHistory.select().where(TransferHistory.to_id == id).order_by(TransferHistory.time.desc())
                     .limit(limit))
    elif message.text.lower().split()[0][-4:] == 'from':
        transfers = (TransferHistory.select().where(TransferHistory.from_id == id).order_by(TransferHistory.time.desc())
                     .limit(limit))
    else:
        transfers = (TransferHistory.select().where((TransferHistory.from_id == id) | (TransferHistory.to_id == id))
                     .order_by(TransferHistory.time.desc()).limit(limit))
    msg = '✝ Общие трансферы пользователя:'
    # edit = await message.reply(msg)
    for i in transfers:
        from_n = await getUserName(i.from_id)
        to_n = await getUserName(i.to_id)
        msg += f'\n F: [id{i.from_id}|{from_n}] | T: [id{i.to_id}|{to_n}] | A: {i.amount} | C: {not bool(i.com)}'
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

    LvlBanned.get_or_create(uid=id)

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

    lb = LvlBanned.get_or_none(LvlBanned.uid == id)
    if lb is None:
        msg = messages.lvlunban_noban()
        await message.reply(msg)
        return
    lb.delete_instance()

    msg = messages.lvlunban()
    await message.reply(msg)


@bl.chat_message(SearchCMD('lvlbanlist'))
async def lvlbanlist(message: Message):
    lvlban = LvlBanned.select()
    msg = f'⚛ Список пользователей в lvlban бота (Всего : {len(lvlban)})\n\n'
    for user in lvlban:
        name = await getUserName(user.uid)
        msg += f"➖ {user.uid} : | [id{user.uid}|{name}]\n"
    await message.reply(msg)
