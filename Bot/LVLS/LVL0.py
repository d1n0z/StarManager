import random
import re
import time
import traceback
from datetime import datetime

from vkbottle import AiohttpClient
from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.rules import SearchCMD
from Bot.tgbot import tgbot
from Bot.utils import (getIDFromMessage, getUserName, getRegDate, kickUser, getUserNickname, getUserAccessLevel,
                       getUserLastMessage, getUserMute, getUserBan, getUserXP, getUserLVL, getUserNeededXP,
                       getUserPremium, getXPTop, uploadImage, addUserXP, isChatAdmin, getUserWarns, getUserMessages,
                       setUserAccessLevel, getChatName, addWeeklyTask, getULvlBanned, getChatSettings, deleteMessages,
                       speccommandscheck, getUserPremmenuSettings, getUserPremmenuSetting)
from config.config import (API, LVL_NAMES, PATH, REPORT_CD, REPORT_TO, COMMANDS, PREMIUM_TASKS_DAILY, TASKS_DAILY,
                           TG_CHAT_ID, TG_TRANSFER_THREAD_ID)
from db import pool
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

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            msgs = await (await c.execute(
                'select uid, messages from messages where uid>0 and messages>0 and chat_id=%s and '
                'uid=ANY(%s) order by messages desc limit 10', (chat_id, members))).fetchall()
    names = await API.users.get(user_ids=[i[0] for i in msgs])

    kb = keyboard.mtop(chat_id, uid)
    msg = messages.mtop(msgs, names)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('stats'))
async def stats(message: Message):
    chat_id = message.peer_id - 2000000000

    if st := await speccommandscheck(message.from_id, 'stats', 15):
        msg = messages.speccommandscooldown(int(15 - (time.time() - st) + 1))
        await message.reply(disable_mentions=1, message=msg)
        return

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

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lvl_name = await (await c.execute('select name from accessnames where chat_id=%s and lvl=%s',
                                              (chat_id, acc))).fetchone()
    lvl_name = lvl_name[0] if lvl_name else LVL_NAMES[acc]

    user = await API.users.get(user_ids=id, fields='photo_max_orig')
    r = await AiohttpClient().request_content(user[0].photo_max_orig)
    with open(PATH + f'media/temp/{id}ava.jpg', "wb") as f:
        f.write(r)
        f.close()

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            invites = await (await c.execute(
                'select count(*) as c from refferal where from_id=%s and chat_id=%s',
                (id, chat_id))).fetchone()
    statsimg = await createStatsImage(
        await getUserWarns(id, chat_id), await getUserMessages(id, chat_id), id, await getUserAccessLevel(id, chat_id),
        await getUserNickname(id, chat_id), await getRegDate(id, '%d.%m.%Y', 'Неизвестно'), last_message, prem, xp,
        userlvl, invites[0], await getUserName(id), top, mute, ban, lvl_name, neededxp,
        await getUserPremmenuSetting(id, 'border_color', False))
    await deleteMessages(reply.conversation_message_id, chat_id)
    await message.reply(disable_mentions=1, attachment=await uploadImage(statsimg))


@bl.chat_message(SearchCMD('report'))
async def report(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.report_empty()
        await message.reply(disable_mentions=1, message=msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            repu = await (await c.execute(
                'select time from reports where uid=%s order by time desc limit 1', (uid,))).fetchone()
    lreptime = 0
    if repu is not None:
        lreptime = repu[0]

    if time.time() - lreptime < REPORT_CD:
        msg = messages.report_cd()
        await message.reply(disable_mentions=1, message=msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            repid = await (await c.execute('select id from reports order by id desc limit 1')).fetchone()
            if repid:
                repid = repid[0] + 1
            else:
                repid = 1
            await c.execute('insert into reports (uid, id, time) VALUES (%s, %s, %s)', (uid, repid, int(time.time())))
            uwarns = await (await c.execute('select warns from reportwarns where uid=%s', (uid,))).fetchone()
            await conn.commit()

    report = ' '.join(data[1:])
    name = await getUserName(uid)
    chat_name = await getChatName(chat_id)
    msg = messages.report(uid, name, report, repid, chat_id, chat_name)
    kb = keyboard.report(uid, repid, chat_id, report)
    
    if uwarns is None or uwarns[0] < 3:
        await API.messages.send(disable_mentions=1, chat_id=REPORT_TO, random_id=0, message=msg, keyboard=kb)
    msg = messages.report_sent(repid)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('help'))
async def help(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cmds = await (await c.execute('select cmd, lvl from commandlevels where chat_id=%s', (chat_id,))).fetchall()
    base = COMMANDS.copy()
    for i in cmds:
        base[i[0]] = int(i[1])
    msg = messages.help(cmds=base)
    u_prem = await getUserPremium(uid)
    kb = keyboard.help(uid, u_prem=u_prem)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('bonus'))
async def bonus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    name = await getUserName(uid)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            bonus = await (await c.execute('select time from bonus where uid=%s', (uid,))).fetchone()
    ltb = bonus[0] if bonus is not None else 0

    if time.time() - ltb < 86400:
        timeleft = ltb + 86400 - time.time()
        msg = messages.bonus_time(uid, None, name, timeleft)
        await message.reply(disable_mentions=1, message=msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update bonus set time = %s where uid=%s', (int(time.time()), uid))).rowcount:
                await c.execute('insert into bonus (uid, time) values (%s, %s)', (uid, int(time.time())))
            await conn.commit()

    await addWeeklyTask(uid, 'bonus')

    u_prem = await getUserPremium(uid)
    addxp = random.randint(10, 50)
    if u_prem:
        addxp = random.randint(50, 100)
    await addUserXP(uid, addxp)

    nickname = await getUserNickname(uid, chat_id)
    msg = messages.bonus(uid, nickname, name, addxp)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('prefix'))
async def prefix(message: Message):
    await message.reply(disable_mentions=1, message=messages.prefix(), keyboard=keyboard.prefix(message.from_id))


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

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                cmdn = await (await c.execute(
                    'select name from cmdnames where uid=%s and cmd=%s', (uid, cmd))).fetchone()
                await c.execute('delete from cmdnames where uid=%s and cmd=%s', (uid, cmd))
                await conn.commit()
        if not cmdn:
            msg = messages.resetcmd_not_changed(cmd)
            await message.reply(disable_mentions=1, message=msg)
            return

        name = await getUserName(uid)
        nick = await getUserNickname(uid, chat_id)
        msg = messages.resetcmd(uid, name, nick, cmd, cmdn[0])
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

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                cmdns = await (await c.execute('select cmd, name from cmdnames where uid=%s', (uid,))).fetchall()
        res = []
        for i in cmdns:
            if i[0] not in res:
                res.append(i[0])
            if changed == i[1]:
                msg = messages.cmd_changed_in_users_cmds(i[0])
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

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute(
                        'update cmdnames set name = %s where uid=%s and cmd=%s', (changed, uid, cmd))).rowcount:
                    await c.execute('insert into cmdnames (uid, cmd, name) values (%s, %s, %s)', (uid, cmd, changed))
                await conn.commit()

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
    settings = await getUserPremmenuSettings(uid)
    msg = messages.premmenu(settings)
    kb = keyboard.premmenu(uid, settings)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('duel'))
async def duel(message: Message):
    chat_id = message.peer_id - 2000000000
    if st := await speccommandscheck(message.from_id, 'duel', 15):
        msg = messages.speccommandscooldown(int(15 - (time.time() - st) + 1))
        await message.reply(disable_mentions=1, message=msg)
        return
    uid = message.from_id

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
    if st := await speccommandscheck(message.from_id, 'transfer', 10):
        msg = messages.speccommandscooldown(int(10 - (time.time() - st) + 1))
        await message.reply(disable_mentions=1, message=msg)
        return
    uid = message.from_id

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
    if await getULvlBanned(id):
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
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute(
                'insert into transferhistory (to_id, from_id, time, amount, com) VALUES (%s, %s, %s, %s, %s)',
                (id, uid, int(time.time()), ftxp, u_prem))
            await conn.commit()
    try:
        await tgbot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_TRANSFER_THREAD_ID,
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
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            t = await c.execute('select count, task from tasksdaily where uid=%s', (uid,))
            for i in await t.fetchall():
                if i[0] >= (TASKS_DAILY | PREMIUM_TASKS_DAILY)[i[1]]:
                    if i[1] in PREMIUM_TASKS_DAILY and not prem:
                        continue
                    completed += 1
            coins = await (await c.execute('select coins from coins where uid=%s', (uid,))).fetchone()
            coins = 0 if coins is None else coins[0]
            streak = await (await c.execute('select streak from tasksstreak where uid=%s', (uid,))).fetchone()
            streak = 0 if streak is None else streak[0]
    kb = keyboard.tasks(uid)
    await message.reply(messages.task(completed, coins, streak), keyboard=kb)


@bl.chat_message(SearchCMD('anon'))
async def anon(message: Message):
    msg = messages.anon_not_pm()
    await message.reply(msg, disable_mentions=1)


@bl.chat_message(SearchCMD('deanon'))
async def deanon(message: Message):
    msg = messages.anon_not_pm()
    await message.reply(msg, disable_mentions=1)
