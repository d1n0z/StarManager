import random
import re
import time
import traceback
from datetime import datetime

from vkbottle import KeyboardButtonColor
from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import getULvlBanned
from Bot.rules import SearchCMD
from Bot.tgbot import tgbot
from Bot.utils import (getIDFromMessage, getUserName, getRegDate, kickUser, getUserNickname, getUserAccessLevel,
                       getUserLastMessage, getUserMute, getUserBan, getUserXP, getUserNeededXP,
                       getUserPremium, uploadImage, addUserXP, isChatAdmin, getUserWarns, getUserMessages,
                       setUserAccessLevel, getChatSettings, deleteMessages,
                       speccommandscheck, getUserPremmenuSettings, getUserPremmenuSetting, chatPremium, getUserLeague,
                       getUserLVL, getUserRep, getRepTop, getChatAccessName, messagereply, pointWords)
from config.config import (GROUP_ID, api, LVL_NAMES, PATH, COMMANDS, TG_CHAT_ID, TG_TRANSFER_THREAD_ID,
                           CMDLEAGUES, DEVS, TG_BONUS_THREAD_ID)
from db import pool
from media.stats.stats_img import createStatsImage

bl = BotLabeler()


@bl.chat_message(SearchCMD('test'))
@bl.chat_message(SearchCMD('chatid'))
async def test_handler(message: Message):
    await messagereply(message, f'💬 ID данной беседы : {message.peer_id - 2000000000}')


@bl.chat_message(SearchCMD('id'))
async def id(message: Message):
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        id = message.from_id
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())

    user = await api.users.get(user_ids=id)
    if user[0].deactivated:
        return await messagereply(message, disable_mentions=1, message=messages.id_deleted())
    await messagereply(message, disable_mentions=1, message=messages.id(
        id, await getRegDate(id), await getUserName(id), f'https://vk.com/id{id}'))


@bl.chat_message(SearchCMD('q'))
async def q(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id

    if await kickUser(uid, chat_id):
        await setUserAccessLevel(uid, chat_id, 0)
        return await messagereply(message, disable_mentions=1, message=messages.q(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id)))
    await messagereply(message, disable_mentions=1, message=messages.q_fail(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id)))


@bl.chat_message(SearchCMD('premium'))
async def premium(message: Message):
    await messagereply(message, disable_mentions=1, message=messages.pm_market(), keyboard=keyboard.pm_market())


@bl.chat_message(SearchCMD('top'))
async def top(message: Message):
    chat_id = message.peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        msgs = await conn.fetch(
            'select uid, messages from messages where uid>0 and messages>0 and chat_id=$1 and '
            'uid=ANY($2) order by messages desc limit 10', chat_id, [i.member_id for i in (
                await api.messages.get_conversation_members(peer_id=message.peer_id)).items])
    await messagereply(message, disable_mentions=1, message=await messages.top(msgs),
                       keyboard=keyboard.top(chat_id, message.from_id))


@bl.chat_message(SearchCMD('stats'))
async def stats(message: Message):
    chat_id = message.peer_id - 2000000000
    if st := await speccommandscheck(message.from_id, 'stats', 15):
        return await messagereply(message, disable_mentions=1, message=messages.speccommandscooldown(
            int(15 - (time.time() - st) + 1)))

    id = await getIDFromMessage(message.text, message.reply_message)
    reply = await messagereply(message, messages.stats_loading(), disable_mentions=1)
    if not id:
        id = message.from_id
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.id_group())

    async with (await pool()).acquire() as conn:
        rewards = await conn.fetchval('select exists(select 1 from rewardscollected where uid=$1 and deactivated=false)', message.from_id)
        acc = await conn.fetchval('select access_level from accesslvl where chat_id=$1 and uid=$2', chat_id, message.from_id) or 0
    if acc < 1 and not await getUserPremium(message.from_id) and not rewards:
        id = message.from_id
    else:
        acc = await getUserAccessLevel(id, chat_id)
    last_message = await getUserLastMessage(id, chat_id)
    if isinstance(last_message, int):
        last_message = datetime.fromtimestamp(last_message).strftime('%d.%m.%Y')
    r = await api.http_client.request_content(
        (await api.users.get(user_ids=id, fields='photo_max_orig'))[0].photo_max_orig)
    with open(PATH + f'media/temp/{id}ava.jpg', "wb") as f:
        f.write(r)

    lvl_name = await getChatAccessName(chat_id, acc)
    xp = int(await getUserXP(id))
    lvl = await getUserLVL(id) or 1
    try:
        await messagereply(message, disable_mentions=1, attachment=await uploadImage(await createStatsImage(
            await getUserWarns(id, chat_id), await getUserMessages(id, chat_id), id,
            await getUserAccessLevel(id, chat_id), await getUserNickname(id, chat_id),
            await getRegDate(id, '%d.%m.%Y', 'Неизвестно'), last_message, await getUserPremium(id),
            min(xp, 99999999), min(lvl, 999), await getUserRep(id), await getRepTop(id), await getUserName(id),
            await getUserMute(id, chat_id), await getUserBan(id, chat_id), lvl_name or LVL_NAMES[acc],
            await getUserNeededXP(xp) if lvl < 999 else 0, await getUserPremmenuSetting(id, 'border_color', False),
            await getUserLeague(id))))
    except Exception as e:
        if message.from_id in DEVS:
            traceback.print_exc()
        await deleteMessages(reply.conversation_message_id, chat_id)
        await messagereply(message, disable_mentions=1, message='❌ Ошибка. Пожалуйста, попробуйте позже.')
        raise e
    else:
        await deleteMessages(reply.conversation_message_id, chat_id)


@bl.chat_message(SearchCMD('help'))
async def help(message: Message):
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        cmds = await conn.fetch('select cmd, lvl from commandlevels where chat_id=$1', message.peer_id - 2000000000)
    base = COMMANDS.copy()
    for i in cmds:
        base[i[0]] = int(i[1])
    await messagereply(message, disable_mentions=1, message=messages.help(cmds=base),
                       keyboard=keyboard.help(uid, u_prem=await getUserPremium(uid)))


@bl.chat_message(SearchCMD('bonus'))
async def bonus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    name = await getUserName(uid)

    async with (await pool()).acquire() as conn:
        lasttime, streak = await conn.fetchrow('select time, streak from bonus where uid=$1', uid) or (0, 0)
    if time.time() - lasttime < 86400:
        return await messagereply(message, disable_mentions=1, message=messages.bonus_time(
            uid, None, name, lasttime + 86400 - time.time()))

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
                'update bonus set time = $1, streak=streak+1 where uid=$2 returning 1', time.time(), uid):
            await conn.execute('insert into bonus (uid, time, streak) values ($1, $2, 1)', uid, time.time())

    prem = await getUserPremium(uid)
    addxp = min(100 + (50 if prem else 25) * streak, 2500 if prem else 1000)
    await addUserXP(uid, addxp)
    await messagereply(message, disable_mentions=1, message=messages.bonus(
        uid, await getUserNickname(uid, chat_id), name, addxp, prem, streak))

    try:
        await tgbot.send_message(
            chat_id=TG_CHAT_ID, message_thread_id=TG_BONUS_THREAD_ID,
            text=f'{uid} | <a href="vk.com/id{uid}">{await getUserName(uid)}</a> | '
                 f'Серия: {pointWords(streak + 1, ("день", "дня", "дней"))}',
            disable_web_page_preview=True, parse_mode='HTML')
    except:
        pass


@bl.chat_message(SearchCMD('prefix'))
async def prefix(message: Message):
    await messagereply(message, disable_mentions=1, message=messages.prefix(),
                       keyboard=keyboard.prefix(message.from_id))


@bl.chat_message(SearchCMD('cmd'))
async def cmd(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.lower().split()
    if len(data) == 2:
        try:
            cmd = data[1]
        except:
            return await messagereply(message, disable_mentions=1, message=messages.resetcmd_hint())
        if cmd not in COMMANDS:
            return await messagereply(message, disable_mentions=1, message=messages.resetcmd_not_found(cmd))

        async with (await pool()).acquire() as conn:
            cmdn = await conn.fetchval('delete from cmdnames where uid=$1 and cmd=$2 returning name', uid, cmd)
        if not cmdn:
            return await messagereply(message, disable_mentions=1, message=messages.resetcmd_not_changed(cmd))

        await messagereply(message, disable_mentions=1, message=messages.resetcmd(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), cmd, cmdn))
    elif len(data) == 3:
        try:
            cmd = data[1]
            changed = ' '.join(data[2:])
        except:
            return await messagereply(message, disable_mentions=1, message=messages.cmd_hint())
        if cmd not in COMMANDS:
            return await messagereply(message, disable_mentions=1, message=messages.resetcmd_not_found(cmd))
        if changed in COMMANDS:
            return await messagereply(message, disable_mentions=1, message=messages.cmd_changed_in_cmds())

        async with (await pool()).acquire() as conn:
            cmdns = await conn.fetch('select cmd, name from cmdnames where uid=$1', uid)
        res = []
        for i in cmdns:
            if i[0] not in res:
                res.append(i[0])
            if changed == i[1]:
                return await messagereply(message, disable_mentions=1, message=messages.cmd_changed_in_users_cmds(i[0]))
        if not await getUserPremium(uid) and len(res) >= CMDLEAGUES[await getUserLeague(uid) - 1]:
            return await messagereply(message, disable_mentions=1, message=messages.cmd_prem(len(res)))

        if len(re.compile(r"[a-zA-Zа-яА-Я0-9]").findall(changed)) != len(changed) or len(changed) > 32:
            return await messagereply(message, disable_mentions=1, message=messages.cmd_char_limit())

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                    'update cmdnames set name = $1 where uid=$2 and cmd=$3 returning 1', changed, uid, cmd):
                await conn.execute('insert into cmdnames (uid, cmd, name) values ($1, $2, $3)', uid, cmd, changed)

        await messagereply(message, disable_mentions=1, message=messages.cmd_set(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), cmd, changed))
    else:
        return await messagereply(message, disable_mentions=1, message=messages.cmd_hint(), keyboard=keyboard.cmd(uid))


@bl.chat_message(SearchCMD('premmenu'))
async def premmenu(message: Message):
    uid = message.from_id
    if not (prem := await getUserPremium(uid)) and await getUserLeague(uid) <= 1:
        return await messagereply(message, disable_mentions=1, message=messages.no_prem())
    settings = await getUserPremmenuSettings(uid)
    await messagereply(message, disable_mentions=1, message=messages.premmenu(settings, prem),
                       keyboard=keyboard.premmenu(uid, settings, prem))


@bl.chat_message(SearchCMD('duel'))
async def duel(message: Message):
    chat_id = message.peer_id - 2000000000
    if st := await speccommandscheck(message.from_id, 'duel', 15):
        return await messagereply(message, disable_mentions=1, message=messages.speccommandscooldown(
            int(15 - (time.time() - st) + 1)))

    if not (await getChatSettings(chat_id))['entertaining']['allowDuel']:
        return await messagereply(message, disable_mentions=1, message=messages.duel_not_allowed())

    data = message.text.split()
    try:
        xp = int(data[1])
    except:
        return await messagereply(message, disable_mentions=1, message=messages.duel_hint())

    if xp < 50 or xp > 500:
        return await messagereply(message, disable_mentions=1, message=messages.duel_xp_minimum())
    if len(data) != 2:
        return await messagereply(message, disable_mentions=1, message=messages.duel_hint())

    uid = message.from_id
    if await getUserXP(uid) < xp:
        return await messagereply(message, disable_mentions=1, message=messages.duel_uxp_not_enough(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id)))

    await messagereply(message, disable_mentions=1, message=messages.duel(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), xp), keyboard=keyboard.duel(uid, xp))


@bl.chat_message(SearchCMD('transfer'))
async def transfer(message: Message):
    chat_id = message.chat_id
    if not (await getChatSettings(chat_id))['entertaining']['allowTransfer']:
        return await messagereply(message, messages.transfer_not_allowed())
    if st := await speccommandscheck(message.from_id, 'transfer', 10):
        return await messagereply(message, disable_mentions=1, message=messages.speccommandscooldown(
            int(10 - (time.time() - st) + 1)))
    uid = message.from_id

    id = await getIDFromMessage(message.text, message.reply_message)
    if id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.transfer_community())
    if not id:
        return await messagereply(message, disable_mentions=1, message=messages.transfer_hint())
    if uid == id:
        return await messagereply(message, disable_mentions=1, message=messages.transfer_myself())
    if await getULvlBanned(id):
        return await messagereply(message, disable_mentions=1, message=messages.user_lvlbanned())

    if (len(message.text.lower().split()) <= 2 and message.reply_message is None) or (
            len(message.text.lower().split()) <= 1 and message.reply_message is not None):
        return await messagereply(message, disable_mentions=1, message=messages.transfer_hint())

    try:
        txp = int(message.text.split()[-1])
    except:
        return await messagereply(message, disable_mentions=1, message=messages.transfer_hint())

    u_prem = await getUserPremium(uid)
    if (txp > 1500 and not u_prem) or (txp > 3000 and u_prem) or txp < 50:
        return await messagereply(message, disable_mentions=1, message=messages.transfer_wrong_number())

    if await getUserXP(uid) < txp:
        return await messagereply(message, disable_mentions=1, message=messages.transfer_not_enough(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id)))

    async with (await pool()).acquire() as conn:
        td = sum([i[0] for i in await conn.fetch(
            'select amount from transferhistory where time>$1 and from_id=$2',
            datetime.now().replace(hour=0, minute=0, second=0).timestamp(), uid)])
    if (td >= 1500 and not u_prem) or (td >= 3000 and not u_prem):
        return await messagereply(message, disable_mentions=1, message=messages.transfer_limit(u_prem))

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
    async with (await pool()).acquire() as conn:
        await conn.execute('insert into transferhistory (to_id, from_id, time, amount, com) VALUES ($1, $2, $3, $4,'
                           ' $5)', id, uid, time.time(), ftxp, u_prem)
    try:
        await tgbot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_TRANSFER_THREAD_ID,
                                 text=f'{chat_id} | <a href="vk.com/id{uid}">{uname}</a> | '
                                      f'<a href="vk.com/id{id}">{name}</a> | {ftxp} | К: {com} | '
                                      f'{datetime.now().strftime("%H:%M:%S")}',
                                 disable_web_page_preview=True, parse_mode='HTML')
    except:
        pass
    await messagereply(message, disable_mentions=1, message=messages.transfer(uid, uname, id, name, ftxp, com))


@bl.chat_message(SearchCMD('start'))
async def start(message: Message):
    chat_id = message.peer_id - 2000000000
    if await getUserAccessLevel(message.from_id, chat_id) >= 7 or await isChatAdmin(message.from_id, chat_id):
        await messagereply(message, messages.rejoin(), keyboard=keyboard.rejoin(chat_id))


@bl.chat_message(SearchCMD('anon'))
async def anon(message: Message):
    await messagereply(message, messages.anon_not_pm(), disable_mentions=1)


@bl.chat_message(SearchCMD('deanon'))
async def deanon(message: Message):
    await messagereply(message, messages.anon_not_pm(), disable_mentions=1)


@bl.chat_message(SearchCMD('chats'))
async def chats(message: Message):
    await messagereply(message, messages.chats(), keyboard=keyboard.chats(), disable_mentions=1)


@bl.chat_message(SearchCMD('guess'))
async def guess(message: Message):
    if st := await speccommandscheck(message.from_id, 'guess', 10):
        return await messagereply(
            message, disable_mentions=1, message=messages.speccommandscooldown(int(10 - (time.time() - st) + 1)))
    if not (await getChatSettings(message.chat_id))['entertaining']['allowGuess']:
        return await messagereply(message, disable_mentions=1, message=messages.guess_not_allowed())
    data = message.text.split()
    if len(data) != 3 or not data[1].isdigit() or not data[2].isdigit() or int(data[2]) < 1 or int(data[2]) > 5:
        return await messagereply(message, disable_mentions=1, message=messages.guess_hint())
    if int(data[1]) < 10 or int(data[1]) > 500:
        return await messagereply(message, disable_mentions=1, message=messages.guess_xp_minimum())
    if await getUserXP(message.from_id) < int(data[1]):
        return await messagereply(message, disable_mentions=1, message=messages.guess_notenoughxp())
    if int(data[2]) != (num := random.randint(1, 5)):
        await addUserXP(message.from_id, -int(data[1]))
        return await messagereply(message, disable_mentions=1, message=messages.guess_lose(data[1], num))
    bet = int(data[1]) * 2.5
    if not (prem := await getUserPremium(message.from_id)):
        bet = bet / 100 * 90
    await addUserXP(message.from_id, bet)
    await messagereply(message, disable_mentions=1, message=messages.guess_win(int(bet), data[2], prem))


@bl.chat_message(SearchCMD('promo'))
async def promo(message: Message):
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(message, disable_mentions=1, message=messages.promo_hint())
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        code = await conn.fetchrow(
            'select code, date, usage, xp from promocodes where code=$1', data[1])
        if code and (code[1] and time.time() > code[1] or (
                code[2] and (len(await conn.fetch(
                    'select id from promocodeuses where code=$1', data[1])) >= code[2]))):
            await conn.execute('delete from promocodes where code=$1', data[1])
            await conn.execute('delete from promocodeuses where code=$1', data[1])
            code = None
        if not code or await conn.fetchval(
                'select exists(select 1 from promocodeuses where code=$1 and uid=$2)', data[1], uid):
            return await messagereply(message, disable_mentions=1, message=messages.promo_alreadyusedornotexists(
                uid, await getUserNickname(uid, message.chat_id), await getUserName(uid)))
        await conn.execute('insert into promocodeuses (code, uid) values ($1, $2)', data[1], uid)
    await addUserXP(uid, int(code[3]))
    await messagereply(message, disable_mentions=1, message=messages.promo(
        uid, await getUserNickname(uid, message.chat_id), await getUserName(uid), code[0], code[3]))


@bl.chat_message(SearchCMD('rep'))
async def rep(message: Message):
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message, 3)
    if len(data) not in (2, 3) or data[1] not in ('+', '-') or not id or id < 0:
        return await messagereply(message, disable_mentions=1, message=messages.rep_hint())
    if id == message.from_id:
        return await messagereply(message, disable_mentions=1, message=messages.rep_myself())
    members = (await api.messages.get_conversation_members(peer_id=message.peer_id)).items
    if len(members) < 2900 and id not in [i.member_id for i in members]:
        return await messagereply(message, disable_mentions=1, message=messages.rep_notinchat())
    uid = message.from_id
    uprem = await getUserPremium(uid)
    async with (await pool()).acquire() as conn:
        rephistory = await conn.fetch('select time from rephistory where uid=$1 and id=$2 and time>$3 order by '
                                      'time', uid, id, time.time() - 86400)
        if len(rephistory) >= (3 if uprem else 1):
            return await messagereply(message, disable_mentions=1, message=messages.rep_limit(uprem, rephistory[0][0]))
        if not await conn.fetchval(f'update reputation set rep=rep {data[1]} 1 where uid=$1 returning 1', id):
            await conn.execute('insert into reputation (uid, rep) values ($1, $2)', id, eval(f'0{data[1]}1'))
        await conn.execute('insert into rephistory (uid, id, time) values ($1, $2, $3)', uid, id, time.time())
    await messagereply(message, disable_mentions=1, message=messages.rep(
        data[1] == '+', uid, await getUserName(uid), await getUserNickname(uid, message.chat_id),
        id, await getUserName(id), await getUserNickname(id, message.chat_id), await getUserRep(id),
        await getRepTop(id)))


@bl.chat_message(SearchCMD('short'))
async def short(message: Message):
    uid = message.from_id
    if not await getUserPremium(uid):
        return await messagereply(message, disable_mentions=1, message=messages.no_prem())
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(message, disable_mentions=1, message=messages.short_hint())
    try:
        shortened = await api.utils.get_short_link(url=data[1], private=0)
        if not shortened or not shortened.short_url:
            raise Exception
    except:
        return await messagereply(message, disable_mentions=1, message=messages.short_failed())
    await messagereply(message, disable_mentions=1, message=messages.short(
        shortened.short_url, (await api.utils.get_short_link(
            f'https://vk.com/cc?act=stats&key={shortened.key}')).short_url))


@bl.chat_message(SearchCMD('rewards'))
async def rewards(message: Message):
    uid = message.from_id
    if not await api.groups.is_member(group_id=GROUP_ID, user_id=uid):
        return await messagereply(
            message, disable_mentions=1, keyboard=keyboard.urlbutton(f'https://vk.com/club{GROUP_ID}', 'Подписаться', KeyboardButtonColor.POSITIVE),
            message=messages.rewards_unsubbed(uid, await getUserName(uid), await getUserNickname(uid, message.chat_id)))
    async with (await pool()).acquire() as conn:
        collected = await conn.fetchrow('select deactivated, date from rewardscollected where uid=$1', uid)
        if collected:
            if collected[0]:
                await conn.fetchrow('update rewardscollected set deactivated=false where uid=$1', uid)
                return await messagereply(
                    message, disable_mentions=1, 
                            message=messages.rewards_activated(uid, await getUserName(uid), await getUserNickname(uid, message.chat_id),
                                                               collected[1], 7))
            return await messagereply(
                message, disable_mentions=1,
                message=messages.rewards_collected(uid, await getUserName(uid), await getUserNickname(uid, message.chat_id),
                                                   datetime.fromtimestamp(collected[1]).strftime('%d.%m.%Y')))
        await conn.execute('insert into rewardscollected (uid, date, deactivated) values ($1, $2, false)', uid, int(time.time()))
    await addUserXP(uid, 10000)
    await messagereply(
        message, disable_mentions=1, 
        message=messages.rewards(uid, await getUserName(uid), await getUserNickname(uid, message.chat_id),
                                 time.time(), 7, 10000))
