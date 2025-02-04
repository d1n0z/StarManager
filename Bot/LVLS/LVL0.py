import random
import re
import time
from datetime import datetime

from vkbottle import AiohttpClient
from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.rules import SearchCMD
from Bot.tgbot import tgbot
from Bot.utils import (getIDFromMessage, getUserName, getRegDate, kickUser, getUserNickname, getUserAccessLevel,
                       getUserLastMessage, getUserMute, getUserBan, getUserXP, getLVLFromXP, getUserNeededXP,
                       getUserPremium, uploadImage, addUserXP, isChatAdmin, getUserWarns, getUserMessages,
                       setUserAccessLevel, getChatName, getULvlBanned, getChatSettings, deleteMessages,
                       speccommandscheck, getUserPremmenuSettings, getUserPremmenuSetting, chatPremium, getURepBanned,
                       getUserLeague, getXPFromLVL, getUserLVL)
from config.config import (API, LVL_NAMES, PATH, REPORT_CD, REPORT_TO, COMMANDS, TG_CHAT_ID, TG_TRANSFER_THREAD_ID,
                           CMDLEAGUES)
from db import pool
from media.stats.stats_img import createStatsImage

bl = BotLabeler()


@bl.chat_message(SearchCMD('test'))
@bl.chat_message(SearchCMD('chatid'))
async def test_handler(message: Message):
    await message.reply(f'💬 ID данной беседы : {message.peer_id - 2000000000}')


@bl.chat_message(SearchCMD('id'))
async def id(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        id = message.from_id
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())

    user = await API.users.get(user_ids=id)
    if user[0].deactivated:
        return await message.reply(disable_mentions=1, message=messages.id_deleted())
    await message.reply(disable_mentions=1, message=messages.id(
        id, await getRegDate(id), await getUserName(id), f'https://vk.com/id{id}'))


@bl.chat_message(SearchCMD('q'))
async def q(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id

    if await kickUser(uid, chat_id):
        await setUserAccessLevel(uid, chat_id, 0)
        return await message.reply(disable_mentions=1, message=messages.q(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id)))
    await message.reply(disable_mentions=1, message=messages.q_fail(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id)))


@bl.chat_message(SearchCMD('premium'))
async def premium(message: Message):
    await message.reply(disable_mentions=1, message=messages.pm_market(), keyboard=keyboard.pm_market())


@bl.chat_message(SearchCMD('top'))
async def top(message: Message):
    chat_id = message.peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            msgs = await (await c.execute(
                'select uid, messages from messages where uid>0 and messages>0 and chat_id=%s and '
                'uid=ANY(%s) order by messages desc limit 10', (chat_id, [i.member_id for i in (
                    await API.messages.get_conversation_members(peer_id=message.peer_id)).items]))).fetchall()
    await message.reply(disable_mentions=1, message=await messages.top(msgs), keyboard=keyboard.top(chat_id, message.from_id))


@bl.chat_message(SearchCMD('stats'))
async def stats(message: Message):
    chat_id = message.peer_id - 2000000000
    if st := await speccommandscheck(message.from_id, 'stats', 15):
        return await message.reply(disable_mentions=1, message=messages.speccommandscooldown(
            int(15 - (time.time() - st) + 1)))

    id = await getIDFromMessage(message.text, message.reply_message)
    reply = await message.reply(messages.stats_loading(), disable_mentions=1)
    if not id:
        id = message.from_id
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())

    acc = await getUserAccessLevel(message.from_id, chat_id)
    if acc < 1 and not await getUserPremium(message.from_id):
        id = message.from_id
    else:
        acc = await getUserAccessLevel(id, chat_id)
    last_message = await getUserLastMessage(id, chat_id)
    if isinstance(last_message, int):
        last_message = datetime.fromtimestamp(last_message).strftime('%d.%m.%Y')
    r = await AiohttpClient().request_content(
        (await API.users.get(user_ids=id, fields='photo_max_orig'))[0].photo_max_orig)
    with open(PATH + f'media/temp/{id}ava.jpg', "wb") as f:
        f.write(r)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lvl_name = await (await c.execute('select name from accessnames where chat_id=%s and lvl=%s',
                                              (chat_id, acc))).fetchone()
            invites = await (await c.execute(
                'select count(*) as c from refferal where from_id=%s and chat_id=%s',
                (id, chat_id))).fetchone()
    xp = int(await getUserXP(id))
    lvl = await getUserLVL(id)
    if not lvl:
        lvl = 1
    await message.reply(disable_mentions=1, attachment=await uploadImage(await createStatsImage(
        await getUserWarns(id, chat_id), await getUserMessages(id, chat_id), id, await getUserAccessLevel(id, chat_id),
        await getUserNickname(id, chat_id), await getRegDate(id, '%d.%m.%Y', 'Неизвестно'), last_message,
        await getUserPremium(id), min(xp, 99999999), min(lvl, 999), invites[0],
        await getUserName(id), await getUserMute(id, chat_id), await getUserBan(id, chat_id),
        lvl_name[0] if lvl_name else LVL_NAMES[acc],
        await getUserNeededXP(xp, lvl) if lvl < 999 else 0,
        await getUserPremmenuSetting(id, 'border_color', False), await getUserLeague(id)), message.peer_id))
    await deleteMessages(reply.conversation_message_id, chat_id)


@bl.chat_message(SearchCMD('report'))
async def report(message: Message):
    uid = message.from_id
    if await getURepBanned(uid):
        return await message.reply(disable_mentions=1, message=messages.repbanned())
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        return await message.reply(disable_mentions=1, message=messages.report_empty())

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            repu = await (await c.execute(
                'select time from reports where uid=%s order by time desc limit 1', (uid,))).fetchone()
    if repu and time.time() - repu[0] < REPORT_CD:
        return await message.reply(disable_mentions=1, message=messages.report_cd())

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            repid = await (await c.execute('select id from reports order by id desc limit 1')).fetchone()
            repid = (repid[0] + 1) if repid else 1
            await c.execute('insert into reports (uid, id, time) VALUES (%s, %s, %s)', (uid, repid, int(time.time())))
            await conn.commit()

    await API.messages.send(disable_mentions=1, chat_id=REPORT_TO, random_id=0, message=messages.report(
        uid, await getUserName(uid), ' '.join(data[1:]), repid, chat_id, await getChatName(chat_id)),
                            keyboard=keyboard.report(uid, repid, chat_id, ' '.join(data[1:])))
    await message.reply(disable_mentions=1, message=messages.report_sent(repid))


@bl.chat_message(SearchCMD('help'))
async def help(message: Message):
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cmds = await (await c.execute('select cmd, lvl from commandlevels where chat_id=%s',
                                          (message.peer_id - 2000000000,))).fetchall()
    base = COMMANDS.copy()
    for i in cmds:
        base[i[0]] = int(i[1])
    await message.reply(disable_mentions=1, message=messages.help(cmds=base),
                        keyboard=keyboard.help(uid, u_prem=await getUserPremium(uid)))


@bl.chat_message(SearchCMD('bonus'))
async def bonus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    name = await getUserName(uid)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            bonus = await (await c.execute('select time from bonus where uid=%s', (uid,))).fetchone()
    if time.time() - (lasttime := bonus[0] if bonus is not None else 0) < (
            reqtime := 28800 if await chatPremium(chat_id) else 86400):
        return await message.reply(disable_mentions=1, message=messages.bonus_time(
            uid, None, name, lasttime + reqtime - time.time()))

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update bonus set time = %s where uid=%s', (int(time.time()), uid))).rowcount:
                await c.execute('insert into bonus (uid, time) values (%s, %s)', (uid, int(time.time())))
            await conn.commit()

    addxp = random.randint(100, 180) if await getUserPremium(uid) else random.randint(20, 100)
    await addUserXP(uid, addxp)
    await message.reply(disable_mentions=1, message=messages.bonus(
        uid, await getUserNickname(uid, chat_id), name, addxp))


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
            return await message.reply(disable_mentions=1, message=messages.resetcmd_hint())
        if cmd not in COMMANDS:
            return await message.reply(disable_mentions=1, message=messages.resetcmd_not_found(cmd))

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                cmdn = await (await c.execute(
                    'select name from cmdnames where uid=%s and cmd=%s', (uid, cmd))).fetchone()
                await c.execute('delete from cmdnames where uid=%s and cmd=%s', (uid, cmd))
                await conn.commit()
        if not cmdn:
            return await message.reply(disable_mentions=1, message=messages.resetcmd_not_changed(cmd))

        await message.reply(disable_mentions=1, message=messages.resetcmd(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), cmd, cmdn[0]))
    elif len(data) == 3:
        try:
            cmd = data[1]
            changed = ' '.join(data[2:])
        except:
            return await message.reply(disable_mentions=1, message=messages.cmd_hint())
        if cmd not in COMMANDS:
            return await message.reply(disable_mentions=1, message=messages.resetcmd_not_found(cmd))
        if changed in COMMANDS:
            return await message.reply(disable_mentions=1, message=messages.cmd_changed_in_cmds())

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                cmdns = await (await c.execute('select cmd, name from cmdnames where uid=%s', (uid,))).fetchall()
        res = []
        for i in cmdns:
            if i[0] not in res:
                res.append(i[0])
            if changed == i[1]:
                return await message.reply(disable_mentions=1, message=messages.cmd_changed_in_users_cmds(i[0]))
        if not await getUserPremium(uid) and len(res) >= CMDLEAGUES[await getUserLeague(uid) - 1]:
            return await message.reply(disable_mentions=1, message=messages.cmd_prem(len(res)))

        if len(re.compile(r"[a-zA-Zа-яА-Я0-9]").findall(changed)) != len(changed) or len(changed) > 32:
            return await message.reply(disable_mentions=1, message=messages.cmd_char_limit())

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute(
                        'update cmdnames set name = %s where uid=%s and cmd=%s', (changed, uid, cmd))).rowcount:
                    await c.execute('insert into cmdnames (uid, cmd, name) values (%s, %s, %s)', (uid, cmd, changed))
                await conn.commit()

        await message.reply(disable_mentions=1, message=messages.cmd_set(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), cmd, changed))
    else:
        return await message.reply(disable_mentions=1, message=messages.cmd_hint(), keyboard=keyboard.cmd(uid))


@bl.chat_message(SearchCMD('premmenu'))
async def premmenu(message: Message):
    uid = message.from_id
    if not (prem := await getUserPremium(uid)) and await getUserLeague(uid) <= 1:
        return await message.reply(disable_mentions=1, message=messages.no_prem())
    settings = await getUserPremmenuSettings(uid)
    await message.reply(disable_mentions=1, message=messages.premmenu(settings, prem),
                        keyboard=keyboard.premmenu(uid, settings, prem))


@bl.chat_message(SearchCMD('duel'))
async def duel(message: Message):
    chat_id = message.peer_id - 2000000000
    if st := await speccommandscheck(message.from_id, 'duel', 15):
        return await message.reply(disable_mentions=1, message=messages.speccommandscooldown(
            int(15 - (time.time() - st) + 1)))

    if not (await getChatSettings(chat_id))['entertaining']['allowDuel']:
        return await message.reply(disable_mentions=1, message=messages.duel_not_allowed())

    data = message.text.split()
    try:
        xp = int(data[1])
    except:
        return await message.reply(disable_mentions=1, message=messages.duel_hint())

    if xp < 50 or xp > 500:
        return await message.reply(disable_mentions=1, message=messages.duel_xp_minimum())
    if len(data) != 2:
        return await message.reply(disable_mentions=1, message=messages.duel_hint())

    uid = message.from_id
    if await getUserXP(uid) < xp:
        return await message.reply(disable_mentions=1, message=messages.duel_uxp_not_enough(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id)))

    await message.reply(disable_mentions=1, message=messages.duel(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), xp), keyboard=keyboard.duel(uid, xp))


@bl.chat_message(SearchCMD('transfer'))
async def transfer(message: Message):
    chat_id = message.chat_id
    if not (await getChatSettings(chat_id))['entertaining']['allowTransfer']:
        return await message.reply(messages.transfer_not_allowed())
    if st := await speccommandscheck(message.from_id, 'transfer', 10):
        return await message.reply(disable_mentions=1, message=messages.speccommandscooldown(
            int(10 - (time.time() - st) + 1)))
    uid = message.from_id

    id = await getIDFromMessage(message.text, message.reply_message)
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.transfer_community())
    if not id:
        return await message.reply(disable_mentions=1, message=messages.transfer_hint())
    if uid == id:
        return await message.reply(disable_mentions=1, message=messages.transfer_myself())
    if await getULvlBanned(id):
        return await message.reply(disable_mentions=1, message=messages.user_lvlbanned())

    if (len(message.text.lower().split()) <= 2 and message.reply_message is None) or (
            len(message.text.lower().split()) <= 1 and message.reply_message is not None):
        return await message.reply(disable_mentions=1, message=messages.transfer_hint())

    try:
        txp = int(message.text.split()[-1])
    except:
        return await message.reply(disable_mentions=1, message=messages.transfer_hint())

    u_prem = await getUserPremium(uid)
    if (txp > 500 and not u_prem) or (txp > 1500 and u_prem) or txp < 50:
        return await message.reply(disable_mentions=1, message=messages.transfer_wrong_number())

    if await getUserXP(uid) < txp:
        return await message.reply(disable_mentions=1, message=messages.transfer_not_enough(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id)))

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            td = sum([i[0] for i in await (
                await c.execute('select amount from transferhistory where time>%s and from_id=%s',
                                (datetime.now().replace(hour=0, minute=0, second=0).timestamp(), uid))).fetchall()])
            if (td >= 1500 and not u_prem) or (td >= 3000 and not u_prem):
                return await message.reply(disable_mentions=1, message=messages.transfer_limit(u_prem))

    if u_prem:
        ftxp = txp
        com = 0
    else:
        if await chatPremium(chat_id):
            ftxp = int(txp / 100 * 97.5)
            com = 2.5
        else:
            ftxp = int(txp / 100 * 95)
            com = 5

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
                                      f'<a href="vk.com/id{id}">{name}</a> | {ftxp} | К: {com} | '
                                      f'{datetime.now().strftime("%H:%M:%S")}',
                                 disable_web_page_preview=True, parse_mode='HTML')
    except:
        pass
    await message.reply(disable_mentions=1, message=messages.transfer(uid, uname, id, name, ftxp, com))


@bl.chat_message(SearchCMD('start'))
async def start(message: Message):
    chat_id = message.peer_id - 2000000000
    if await getUserAccessLevel(message.from_id, chat_id) >= 7 or await isChatAdmin(message.from_id, chat_id):
        await message.reply(messages.rejoin(), keyboard=keyboard.rejoin(chat_id))


@bl.chat_message(SearchCMD('anon'))
async def anon(message: Message):
    await message.reply(messages.anon_not_pm(), disable_mentions=1)


@bl.chat_message(SearchCMD('deanon'))
async def deanon(message: Message):
    await message.reply(messages.anon_not_pm(), disable_mentions=1)


@bl.chat_message(SearchCMD('chats'))
async def chats(message: Message):
    await message.reply(messages.chats(), keyboard=keyboard.chats(), disable_mentions=1)
