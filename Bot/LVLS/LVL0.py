import random
import re
import time
import traceback
from datetime import datetime

import requests
from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.rules import SearchCMD
from Bot.tgbot import getTGBot
from Bot.utils import (getIDFromMessage, getUserName, getRegDate, kickUser, getUserNickname, getUserAccessLevel,
                       getUserLastMessage, getUserMute, getUserBan, getUserXP, getUserLVL, getUserNeededXP,
                       getUserPremium, getXPTop, uploadImage, addUserXP, isChatAdmin, getUserWarns, getUserMessages,
                       setUserAccessLevel, getChatName, addWeeklyTask, getULvlBanned, getChatSettings)
from config.config import (API, LVL_NAMES, PATH, REPORT_CD, REPORT_TO, COMMANDS, DEVS, PREMIUM_TASKS_DAILY, TASKS_DAILY,
                           TG_CHAT_ID, TG_TRANSFER_THREAD_ID)
from db import (Messages, AccessNames, Referral, Reports, ReportWarns, CMDLevels, Bonus, Prefixes, CMDNames, PremMenu,
                TasksDaily, Coins, TasksStreak, TransferHistory, SpecCommandsCooldown)
from media.stats.stats_img import createStatsImage

bl = BotLabeler()


@bl.chat_message(SearchCMD('test'))
async def test_handler(message: Message):
    chat_id = message.peer_id - 2000000000
    await message.reply(f'💬 ID данной беседы : {chat_id}')


@bl.chat_message(SearchCMD('chatid'))
async def chatid(message: Message):
    await message.reply(f'💬 ID данной беседы : {message.peer_id - 2000000000}')


@bl.chat_message(SearchCMD('id'))
async def id(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)

    if not id:
        id = message.from_id
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    user = await API.users.get(user_ids=id)
    if user[0].deactivated:
        msg = messages.id_deleted()
        await message.reply(disable_mentions=1, message=msg)
        return

    url = f'https://vk.com/id{id}'
    data = await getRegDate(id)
    name = await getUserName(id)

    msg = messages.id(id, data, name, url)
    await message.reply(disable_mentions=1, message=msg)
    return


@bl.chat_message(SearchCMD('q'))
async def q(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id

    await setUserAccessLevel(uid, chat_id, 0)
    kick_res = await kickUser(uid, chat_id)
    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)
    if kick_res:
        msg = messages.q(uid, name, nick)
    else:
        msg = messages.q_fail(uid, name, nick)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('premium'))
async def premium(message: Message):
    try:
        msg = messages.pm_market()
        kb = keyboard.pm_market()
        await message.reply(disable_mentions=1, message=msg, keyboard=kb)
    except:
        pass


@bl.chat_message(SearchCMD('mtop'))
async def mtop(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = [int(i.member_id) for i in members.items]

    msgs = Messages.select().where(Messages.uid > 0, Messages.messages > 0, Messages.chat_id == chat_id,
                                   Messages.uid << members).order_by(Messages.messages.desc()).limit(10)
    names = await API.users.get(user_ids=[i.uid for i in msgs])

    kb = keyboard.mtop(chat_id, uid)
    msg = messages.mtop(msgs, names)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('stats'))
async def stats(message: Message):
    chat_id = message.peer_id - 2000000000

    if s := SpecCommandsCooldown.get_or_none(SpecCommandsCooldown.uid == message.from_id,
                                             SpecCommandsCooldown.time > time.time() - 15,
                                             SpecCommandsCooldown.cmd == 'stats'):
        msg = messages.speccommandscooldown(int(15 - (time.time() - s.time) + 1))
        await message.reply(disable_mentions=1, message=msg)
        return
    SpecCommandsCooldown.create(time=time.time(), uid=message.from_id, cmd='stats')

    id = await getIDFromMessage(message.text, message.reply_message)
    reply = await message.reply(messages.stats_loading(), disable_mentions=1)
    if not id:
        id = message.from_id
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    acc = await getUserAccessLevel(message.from_id, chat_id)
    if acc < 1 and not await getUserPremium(message.from_id):
        id = message.from_id
    else:
        acc = await getUserAccessLevel(id, chat_id)
    last_message = await getUserLastMessage(id, chat_id)
    if isinstance(last_message, int):
        last_message = datetime.fromtimestamp(last_message).strftime('%d.%m.%Y')
    mute = await getUserMute(id, chat_id)
    ban = await getUserBan(id, chat_id)
    xp = await getUserXP(id)
    userlvl = await getUserLVL(xp)
    neededxp = await getUserNeededXP(xp)
    prem = await getUserPremium(id)

    top = await getXPTop()
    top = top.get(id) if id in top else len(top)

    lvl_name = AccessNames.get_or_none(AccessNames.chat_id == chat_id, AccessNames.lvl == acc)
    if lvl_name is not None:
        lvl_name = lvl_name.name
    else:
        lvl_name = LVL_NAMES[acc]

    user = await API.users.get(user_ids=id, fields='photo_max_orig')
    r = requests.get(user[0].photo_max_orig)
    with open(PATH + f'media/temp/{id}ava.jpg', "wb") as f:
        f.write(r.content)
        f.close()
    r.close()

    invites = len(Referral.select().where(Referral.from_id == id, Referral.chat_id == chat_id))
    date = await getRegDate(id, '%d.%m.%Y', 'Неизвестно')
    name = await getUserName(id)
    warns = await getUserWarns(id, chat_id)
    messages_count = await getUserMessages(id, chat_id)
    access_level = await getUserAccessLevel(id, chat_id)
    nickname = await getUserNickname(id, chat_id)
    statsimg = await createStatsImage(warns, messages_count, id, access_level, nickname, date, last_message, prem, xp,
                                      userlvl, invites, name, top, mute, ban, lvl_name, neededxp)
    await API.messages.edit(peer_id=message.peer_id, conversation_message_id=reply.conversation_message_id,
                            disable_mentions=1, attachment=await uploadImage(statsimg))


@bl.chat_message(SearchCMD('report'))
async def report(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.report_empty()
        await message.reply(disable_mentions=1, message=msg)
        return

    repu = Reports.select().where(Reports.uid == uid).order_by(Reports.time.desc()).get_or_none()
    lreptime = 0
    if repu is not None:
        lreptime = repu.time

    if time.time() - lreptime < REPORT_CD:
        msg = messages.report_cd()
        await message.reply(disable_mentions=1, message=msg)
        return

    repid = Reports.select().order_by(Reports.id.desc()).get_or_none()
    repid = repid.id + 1

    Reports.create(uid=uid, id=repid, time=time.time())

    report = ' '.join(data[1:])
    name = await getUserName(uid)
    chat_name = await getChatName(chat_id)
    msg = messages.report(uid, name, report, repid, chat_id, chat_name)
    kb = keyboard.report(uid, repid, chat_id, report)

    uwarns = ReportWarns.get_or_none(ReportWarns.uid == uid)
    if uwarns is None or uwarns.warns < 3:
        await API.messages.send(disable_mentions=1, chat_id=REPORT_TO, random_id=0, message=msg, keyboard=kb)
    msg = messages.report_sent(repid)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('help'))
async def help(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    cmds = CMDLevels.select().where(CMDLevels.chat_id == chat_id)
    base = COMMANDS.copy()
    for i in cmds:
        try:
            base[i.cmd] = int(i.lvl)
        except:
            pass
    msg = messages.help(cmds=base)
    u_prem = await getUserPremium(uid)
    kb = keyboard.help(uid, u_prem=u_prem)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('bonus'))
async def bonus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    name = await getUserName(uid)

    bonus = Bonus.get_or_none(Bonus.uid == uid)
    ltb = 0
    if bonus is not None:
        ltb = bonus.time

    if time.time() - ltb < 86400:
        timeleft = ltb + 86400 - time.time()
        msg = messages.bonus_time(uid, None, name, timeleft)
        await message.reply(disable_mentions=1, message=msg)
        return

    bonus = Bonus.get_or_create(uid=uid, defaults={'time': 0})[0]
    bonus.time = time.time()
    bonus.save()

    await addWeeklyTask(uid, 'bonus')

    u_prem = await getUserPremium(uid)
    addxp = random.randint(10, 50)
    if u_prem:
        addxp = random.randint(50, 100)
    await addUserXP(uid, addxp)

    nickname = await getUserNickname(uid, chat_id)
    msg = messages.bonus(uid, nickname, name, addxp)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('addprefix'))
async def addprefix(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()

    if len(data) != 2:
        msg = messages.addprefix_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if len(data[1]) > 2:
        msg = messages.addprefix_too_long()
        await message.reply(disable_mentions=1, message=msg)
        return

    if len(Prefixes.select().where(Prefixes.uid == uid)) >= 3:
        msg = messages.addprefix_max()
        await message.reply(disable_mentions=1, message=msg)
        return

    Prefixes.get_or_create(uid=uid, prefix=data[1])

    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)
    msg = messages.addprefix(uid, name, nick, data[1])
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('delprefix'))
async def delprefix(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    if len(data) < 2:
        msg = messages.delprefix_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    pr = Prefixes.get_or_none(Prefixes.uid == uid, Prefixes.prefix == data[1])
    if pr is None:
        msg = messages.delprefix_not_found(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return
    pr.delete_instance()

    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)
    msg = messages.delprefix(uid, name, nick, data[1])
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('listprefix'))
async def listprefix(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if int(u_prem) <= 0:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    prefixes = Prefixes.select().where(Prefixes.uid == uid)

    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)
    msg = messages.listprefix(uid, name, nick, prefixes)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('cmd'))
async def cmd(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.lower().split()
    if len(data) == 2:
        try:
            cmd = data[1]
        except:
            msg = messages.resetcmd_hint()
            await message.reply(disable_mentions=1, message=msg)
            return
        if cmd not in COMMANDS:
            msg = messages.resetcmd_not_found(cmd)
            await message.reply(disable_mentions=1, message=msg)
            return

        cmdn = CMDNames.get_or_none(CMDNames.uid == uid, CMDNames.cmd == cmd)
        if cmdn is None:
            msg = messages.resetcmd_not_changed(cmd)
            await message.reply(disable_mentions=1, message=msg)
            return
        cmdname = cmdn.name
        cmdn.delete_instance()

        name = await getUserName(uid)
        nick = await getUserNickname(uid, chat_id)
        msg = messages.resetcmd(uid, name, nick, cmd, cmdname)
        await message.reply(disable_mentions=1, message=msg)
    elif len(data) == 3:
        try:
            cmd = data[1]
            changed = ' '.join(data[2:])
        except:
            msg = messages.cmd_hint()
            await message.reply(disable_mentions=1, message=msg)
            return
        if cmd not in COMMANDS:
            msg = messages.resetcmd_not_found(cmd)
            await message.reply(disable_mentions=1, message=msg)
            return
        if changed in COMMANDS:
            msg = messages.cmd_changed_in_cmds()
            await message.reply(disable_mentions=1, message=msg)
            return

        res = []
        for i in CMDNames.select().where(CMDNames.uid == uid):
            if i.cmd not in res:
                res.append(i.cmd)
            if changed == i.name:
                msg = messages.cmd_changed_in_users_cmds(i.cmd)
                await message.reply(disable_mentions=1, message=msg)
                return
        u_prem = await getUserPremium(uid)
        if len(res) >= 10 and u_prem == 0:
            msg = messages.cmd_prem()
            await message.reply(disable_mentions=1, message=msg)
            return

        pattern = re.compile(r"[a-zA-Zа-яА-Я0-9]")
        if len(pattern.findall(changed)) != len(changed) or len(changed) > 32:
            msg = messages.cmd_char_limit()
            await message.reply(disable_mentions=1, message=msg)
            return

        cmdn = CMDNames.get_or_create(uid=uid, cmd=cmd)[0]
        cmdn.name = changed
        cmdn.save()

        name = await getUserName(uid)
        nick = await getUserNickname(uid, chat_id)
        msg = messages.cmd_set(uid, name, nick, cmd, changed)
        await message.reply(disable_mentions=1, message=msg)
    else:
        msg = messages.cmd_hint()
        kb = keyboard.cmd(uid)
        await message.reply(disable_mentions=1, message=msg, keyboard=kb)
        return


@bl.chat_message(SearchCMD('premmenu'))
async def premmenu(message: Message):
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return
    settings = {}
    pm = PremMenu.get_or_none(PremMenu.uid == uid, PremMenu.setting == 'clear_by_fire')
    settings['clear_by_fire'] = True
    if pm is not None:
        settings['clear_by_fire'] = pm.pos
    settings['border_color'] = True
    msg = messages.premmenu(settings)
    kb = keyboard.premmenu(uid, settings)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('duel'))
async def duel(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id

    if s := SpecCommandsCooldown.get_or_none(SpecCommandsCooldown.uid == uid,
                                             SpecCommandsCooldown.time > time.time() - 15,
                                             SpecCommandsCooldown.cmd == 'duel'):
        msg = messages.speccommandscooldown(int(15 - (time.time() - s.time) + 1))
        await message.reply(disable_mentions=1, message=msg)
        return
    SpecCommandsCooldown.create(time=time.time(), uid=uid, cmd='duel')

    if not (await getChatSettings(chat_id))['entertaining']['allowDuel']:
        msg = messages.duel_not_allowed()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    try:
        xp = int(data[1])
    except:
        msg = messages.duel_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if xp < 50 or xp > 500:
        msg = messages.duel_xp_minimum()
        await message.reply(disable_mentions=1, message=msg)
        return
    if len(data) != 2:
        msg = messages.duel_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    uxp = await getUserXP(uid)
    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)

    if uxp < xp:
        msg = messages.duel_uxp_not_enough(uid, name, nick)
        await message.reply(disable_mentions=1, message=msg)
        return

    msg = messages.duel(uid, name, nick, xp)
    kb = keyboard.duel(uid, xp)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('transfer'))
async def transfer(message: Message):
    chat_id = message.chat_id
    if not (await getChatSettings(chat_id))['entertaining']['allowTransfer']:
        await message.reply(messages.transfer_not_allowed())
        return
    uid = message.from_id

    if s := SpecCommandsCooldown.get_or_none(SpecCommandsCooldown.uid == uid,
                                             SpecCommandsCooldown.time > time.time() - 10,
                                             SpecCommandsCooldown.cmd == 'transfer'):
        s: SpecCommandsCooldown
        msg = messages.speccommandscooldown(int(10 - (time.time() - s.time) + 1))
        await message.reply(disable_mentions=1, message=msg)
        return
    SpecCommandsCooldown.create(time=time.time(), uid=uid, cmd='transfer')

    id = await getIDFromMessage(message.text, message.reply_message)
    if id < 0:
        msg = messages.transfer_community()
        await message.reply(disable_mentions=1, message=msg)
        return
    if not id:
        msg = messages.transfer_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.transfer_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if not await getULvlBanned(id):
        msg = messages.user_lvlbanned()
        await message.reply(disable_mentions=1, message=msg)
        return

    if (len(message.text.lower().split()) <= 2 and message.reply_message is None) or (
            len(message.text.lower().split()) <= 1 and message.reply_message is not None):
        msg = messages.transfer_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        txp = int(message.text.split()[-1])
    except:
        msg = messages.transfer_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    u_prem = await getUserPremium(uid)
    if (txp > 500 and int(u_prem) == 0) or (txp > 1500 and int(u_prem) != 0) or txp < 50:
        msg = messages.transfer_wrong_number()
        await message.reply(disable_mentions=1, message=msg)
        return

    if await getUserXP(uid) < txp:
        nickname = await getUserNickname(uid, chat_id)
        name = await getUserName(uid)
        msg = messages.transfer_not_enough(uid, name, nickname)
        await message.reply(disable_mentions=1, message=msg)
        return

    if not u_prem:
        ftxp = int(txp / 100 * 95)
    else:
        ftxp = txp

    await addUserXP(uid, -txp)
    await addUserXP(id, ftxp)
    uname = await getUserName(uid)
    name = await getUserName(id)
    TransferHistory.create(to_id=id, from_id=uid, time=time.time(), amount=ftxp, com=bool(u_prem))
    try:
        bot = getTGBot()
        await bot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_TRANSFER_THREAD_ID,
                               text=f'{chat_id} | <a href="vk.com/id{uid}">{uname}</a> | '
                                    f'<a href="vk.com/id{id}">{name}</a> | {ftxp} | К: {not u_prem} | '
                                    f'{datetime.now().strftime("%H:%M:%S")}',
                               disable_web_page_preview=True, parse_mode='HTML')
    except:
        traceback.print_exc()

    msg = messages.transfer(uid, uname, id, name, ftxp, u_prem)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('start'))
async def start(message: Message):
    chat_id = message.peer_id - 2000000000
    acc = await getUserAccessLevel(message.from_id, chat_id)
    if acc >= 7 or await isChatAdmin(message.from_id, chat_id):
        msg = messages.rejoin()
        kb = keyboard.rejoin(chat_id)
        await message.reply(msg, keyboard=kb)


@bl.chat_message(SearchCMD('task'))
async def task(message: Message):
    chat_id = message.chat_id
    if not (await getChatSettings(chat_id))['entertaining']['allowTask']:
        await message.reply(messages.task_not_allowed())
        return
    uid = message.from_id
    completed = 0
    prem = await getUserPremium(uid)
    t = TasksDaily.select().where(TasksDaily.uid == uid)
    for i in t:
        if i.count >= (TASKS_DAILY | PREMIUM_TASKS_DAILY)[i.task]:
            if i.task in PREMIUM_TASKS_DAILY and not prem:
                continue
            completed += 1
    c = Coins.get_or_none(Coins.uid == uid)
    c = c.coins if c is not None else 0
    s = TasksStreak.get_or_none(TasksStreak.uid == uid)
    s = s.streak if s is not None else 0
    kb = keyboard.tasks(uid)
    await message.reply(messages.task(completed, c, s), keyboard=kb)


@bl.chat_message(SearchCMD('anon'))
async def anon(message: Message):
    msg = messages.anon_not_pm()
    await message.reply(msg, disable_mentions=1)
