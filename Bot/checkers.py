from datetime import datetime

from cache.async_ttl import AsyncTTL

import messages
from Bot.utils import getUserAccessLevel, getUserPremium, getUserLastMessage, getUserMute, getChatSettings, \
    deleteMessages, getUserPrefixes, getSilence, getSilenceAllowed, messagereply
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
    async with (await pool()).acquire() as conn:
        ugw = await conn.fetchval('select time from globalwarns where uid=$1', uid)
    if ugw is not None and ugw > msgtime:
        return True
    return False


async def haveAccess(cmd, chat_id, uacc, premium=0) -> int | bool:
    async with (await pool()).acquire() as conn:
        cmdacc = await conn.fetchval('select lvl from commandlevels where chat_id=$1 and cmd=$2', chat_id, cmd)
    if cmd == 'check' and premium:
        return True
    if cmdacc is not None:
        return cmdacc <= uacc
    try:
        return COMMANDS[cmd] <= uacc
    except:
        return 7 <= uacc


@AsyncTTL(maxsize=0)
async def getUserIgnore(uid, chat_id) -> bool:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select exists(select 1 from ignore where chat_id=$1 and uid=$2)', chat_id, uid)


@AsyncTTL(maxsize=0)
async def getUInfBanned(uid, chat_id) -> bool:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval("select exists(select 1 from blocked where (uid=$1 and type='chat') or "
                                   "(uid=$2 and type='user'))", chat_id, uid)


@AsyncTTL(maxsize=0)
async def getULvlBanned(uid) -> bool:
    if await getUInfBanned(uid, None):
        return True
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select exists(select 1 from lvlbanned where uid=$1)', uid)


async def getUChatLimit(msgtime, last_message, u_acc, chat_id) -> bool:
    if u_acc >= 6:
        return False
    async with (await pool()).acquire() as conn:
        chl = await conn.fetchval('select time from chatlimit where chat_id=$1', chat_id)
    if not chl or msgtime - last_message >= chl:
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

    async with (await pool()).acquire() as conn:
        if text[:1] in PREFIX:
            prefix = text[:1]
        else:
            prefix = await conn.fetchval(
                'select prefix from prefix where uid=$1 and prefix=ANY($2)', uid, [text[:1], text[:2]])
        if not prefix:
            return False

        if (cmd := text.replace(prefix, '', 1)) in COMMANDS:
            pass
        elif cmd := await conn.fetchval('select cmd from cmdnames where uid=$1 and name=$2', uid, cmd):
            pass
        else:
            if (cmd in PM_COMMANDS or text.replace(prefix, '', 1) in PM_COMMANDS) and message.peer_id >= 2000000000:
                await messagereply(message, messages.pmcmd())
            return False

    if fixing and uid not in (DEVS if accesstoalldevs else MAIN_DEVS):
        await messagereply(message, disable_mentions=1, message=messages.inprogress())
        return False

    u_acc = await getUserAccessLevel(uid, chat_id)
    u_prem = await getUserPremium(uid)
    if (not await haveAccess(cmd, chat_id, u_acc, u_prem) or
            prefix not in await getUserPrefixes(u_prem, uid) or await getUserMute(uid, chat_id) > message.date or
            await getUserIgnore(uid, chat_id) or await getUInfBanned(uid, chat_id) or
            (await getSilence(chat_id) and u_acc not in await getSilenceAllowed(chat_id)) or
            await getUChatLimit(message.date, await getUserLastMessage(uid, chat_id, 0), u_acc, chat_id)):
        return False

    if cmd in LVL_BANNED_COMMANDS and await getULvlBanned(uid):
        await messagereply(message, messages.lvlbanned())
        return False

    settings = await getChatSettings(chat_id)
    if settings['main']['nightmode'] and u_acc < 6:
        async with (await pool()).acquire() as conn:
            setting = await conn.fetchval(
                'select value2 from settings where chat_id=$1 and setting=\'nightmode\'', chat_id)
        if setting:
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
            async with (await pool()).acquire() as conn:
                if await conn.fetchval(
                        'select exists(select id from typequeue where chat_id=$1 and uid=$2 and type=\'captcha\')',
                        chat_id, uid):
                    return False

    if returncmd:
        return cmd
    return True
