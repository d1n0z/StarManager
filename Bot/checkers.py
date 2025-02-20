import traceback
from datetime import datetime

from cache.async_ttl import AsyncTTL

import messages
from Bot.utils import getUserAccessLevel, getUserPremium, getUserLastMessage, getUserMute, getChatSettings, \
    deleteMessages
from config.config import COMMANDS, api, PREFIX, DEVS, MAIN_DEVS, LVL_BANNED_COMMANDS, PM_COMMANDS
from db import pool


@AsyncTTL(time_to_live=30, maxsize=0)
async def isAdmin(chat_id) -> bool:
    try:
        await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        return True
    except:
        return False


async def isSGW(uid, msgtime) -> bool:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            ugw = await (await c.execute('select time from globalwarns where uid=%s', (uid,))).fetchone()
    if ugw and ugw[0] > msgtime:
        return True
    return False


async def haveAccess(cmd, chat_id, uacc, premium=0) -> int | bool:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cmdacc = await (await c.execute(
                'select lvl from commandlevels where chat_id=%s and cmd=%s', (chat_id, cmd))).fetchone()
    if cmd == 'check' and premium:
        return True
    if cmdacc is not None:
        return cmdacc[0] <= uacc
    try:
        return COMMANDS[cmd] <= uacc
    except:
        return 7 <= uacc


async def getUserPrefixes(u_prem, uid) -> list:
    if u_prem:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                prefixes = await (await c.execute('select prefix from prefix where uid=%s', (uid,))).fetchall()
        return PREFIX + [i[0] for i in prefixes]
    return PREFIX


@AsyncTTL(maxsize=0)
async def getUserIgnore(uid, chat_id) -> bool:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            return bool(await (await c.execute('select id from ignore where chat_id=%s and uid=%s',
                                               (chat_id, uid))).fetchone())


@AsyncTTL(maxsize=0)
async def getUInfBanned(uid, chat_id) -> bool:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            return bool(await (await c.execute('select id from infbanned where uid=ANY(%s)',
                                               ([chat_id, uid],))).fetchone())


@AsyncTTL(maxsize=0)
async def getULvlBanned(uid) -> bool:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            return bool(await (await c.execute('select id from lvlbanned where uid=%s', (uid,))).fetchone())


async def getUChatLimit(msgtime, last_message, u_acc, chat_id) -> bool:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chl = await (await c.execute('select time from chatlimit where chat_id=%s', (chat_id,))).fetchone()
    if not chl or not chl[0] or msgtime - last_message >= chl[0] or u_acc >= 6:
        return False
    return True


async def checkCMD(message, chat_id, fixing=False, accesstoalldevs=False, returncmd=False) -> bool | str:
    uid = message.from_id
    if uid < 0:
        return False
    try:
        text = message.text.lower().split()[0]
    except:
        return False

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if text[:1] in PREFIX:
                prefix = text[:1]
            elif prefix := await (await c.execute('select prefix from prefix where uid=%s and prefix=ANY(%s)',
                                                  (uid, [text[:1], text[:2]]))).fetchone():
                prefix = prefix[0]
            else:
                return False

            if text.replace(prefix, '', 1) in COMMANDS:
                cmd = text.replace(prefix, '', 1)
            elif cmd := await (await c.execute('select cmd from cmdnames where uid=%s and name=%s',
                                               (uid, text.replace(prefix, '', 1)))).fetchone():
                cmd = cmd[0]
            else:
                if (cmd in PM_COMMANDS or text.replace(prefix, '', 1) in PM_COMMANDS) and message.peer_id >= 2000000000:
                    await message.reply(messages.pmcmd())
                return False

    if cmd in LVL_BANNED_COMMANDS and await getULvlBanned(uid):
        await message.reply(messages.lvlbanned())
        return False

    if fixing and uid not in (DEVS if accesstoalldevs else MAIN_DEVS):
        await message.reply(disable_mentions=1, message=messages.inprogress())
        return False

    u_acc = await getUserAccessLevel(uid, chat_id)
    u_prem = await getUserPremium(uid)
    if ((not await haveAccess(cmd, chat_id, u_acc, u_prem)) or
            (prefix not in await getUserPrefixes(u_prem, uid)) or
            (await getUserMute(uid, chat_id) > message.date) or
            (await getUserIgnore(uid, chat_id)) or
            (await getUInfBanned(uid, chat_id)) or
            (await getUChatLimit(message.date, await getUserLastMessage(uid, chat_id, 0), u_acc, chat_id))):
        return False
    settings = await getChatSettings(chat_id)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if settings['main']['nightmode'] and u_acc < 6:
                chatsetting = await (await c.execute(
                    'select value2 from settings where chat_id=%s and setting=\'nightmode\'', (chat_id,))).fetchone()
                if chatsetting and (setting := chatsetting[0]):
                    setting = setting.split('-')
                    now = datetime.now()
                    start = datetime.strptime(setting[0], '%H:%M').replace(year=now.year)
                    end = datetime.strptime(setting[1], '%H:%M').replace(year=now.year)
                    if not (now.hour < start.hour or now.hour > end.hour or (
                            now.hour == start.hour and now.minute < start.minute) or (
                                    now.hour == end.hour and now.minute >= end.minute)):
                        await deleteMessages(message.conversation_message_id, chat_id)
                        return False

            if settings['main']['captcha']:
                if await (await c.execute('select id from typequeue where chat_id=%s and uid=%s and type=\'captcha\'',
                                          (chat_id, uid))).fetchone():
                    return False

    if returncmd:
        return cmd
    return True
