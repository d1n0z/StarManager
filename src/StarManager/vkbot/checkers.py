import time

from cache.async_ttl import AsyncTTL

import StarManager.vkbot.messages as messages
from StarManager.core.utils import (
    command_cooldown_check,
    get_chat_settings,
    get_silence,
    get_silence_allowed,
    get_user_access_level,
    get_user_last_message,
    get_user_mute,
    get_user_prefixes,
    get_user_premium,
    messagereply,
)
from StarManager.core.config import settings
from StarManager.core.db import pool


async def haveAccess(cmd, chat_id, uacc, premium=0) -> int | bool:
    async with (await pool()).acquire() as conn:
        cmdacc = await conn.fetchval(
            "select lvl from commandlevels where chat_id=$1 and cmd=$2", chat_id, cmd
        )
    if cmd == "check" and premium:
        return True
    if cmdacc is not None:
        return cmdacc <= uacc
    try:
        return settings.commands.commands[cmd] <= uacc
    except Exception:
        return 7 <= uacc


@AsyncTTL(maxsize=0)
async def getUserIgnore(uid, chat_id) -> bool:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            "select exists(select 1 from ignore where chat_id=$1 and uid=$2)",
            chat_id,
            uid,
        )


@AsyncTTL(maxsize=0)
async def getUInfBanned(uid, chat_id) -> bool:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            "select exists(select 1 from blocked where (uid=$1 and type='chat') or "
            "(uid=$2 and type='user'))",
            chat_id,
            uid,
        )


@AsyncTTL(maxsize=0)
async def getULvlBanned(uid) -> bool:
    if await getUInfBanned(uid, None):
        return True
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            "select exists(select 1 from lvlbanned where uid=$1)", uid
        )


async def getUChatLimit(msgtime, last_message, u_acc, chat_id) -> bool:
    if u_acc >= 6:
        return False
    async with (await pool()).acquire() as conn:
        chl = await conn.fetchval(
            "select time from chatlimit where chat_id=$1", chat_id
        )
    if not chl or msgtime - last_message >= chl:
        return False
    return True


async def checkCMD(
    message, chat_id, fixing=False, accesstoalldevs=False, returncmd=False
) -> bool | str:
    uid = message.from_id
    if uid < 0:
        return False
    try:
        text = message.text.lower().split()[0]
    except Exception:
        return False

    print(211)
    async with (await pool()).acquire() as conn:
        if text[:1] in settings.commands.prefix:
            prefix = text[:1]
        else:
            prefix = await conn.fetchval(
                "select prefix from prefix where uid=$1 and prefix=ANY($2)",
                uid,
                [text[:1], text[:2]],
            )
        if not prefix:
            return False

        raw = text.replace(prefix, "", 1)

        if raw in settings.commands.commands:
            cmd = raw
        else:
            db_cmd = await conn.fetchval(
                "select cmd from cmdnames where uid=$1 and name=$2", uid, raw
            )
            if db_cmd:
                cmd = db_cmd
            else:
                if raw in settings.commands.pm and message.peer_id >= 2000000000:
                    await messagereply(message, await messages.pmcmd())
                return False
    print(212)

    if raw in settings.commands.pm:
        if message.peer_id >= 2000000000:
            await messagereply(message, await messages.pmcmd())
        return False

    if fixing and uid not in (
        settings.service.devs if accesstoalldevs else settings.service.main_devs
    ):
        await messagereply(
            message, disable_mentions=1, message=await messages.inprogress()
        )
        return False

    if st := await command_cooldown_check(message.from_id, cmd):
        await messagereply(
            message,
            disable_mentions=1,
            message=await messages.commandcooldown(
                int(settings.commands.cooldown[cmd] - (time.time() - st) + 1)
            ),
        )
        return False
    print(213)

    u_acc = await get_user_access_level(uid, chat_id)
    u_prem = await get_user_premium(uid)
    if (
        not await haveAccess(cmd, chat_id, u_acc, u_prem)
        or prefix not in await get_user_prefixes(u_prem, uid)
        or await get_user_mute(uid, chat_id) > message.date
        or await getUserIgnore(uid, chat_id)
        or await getUInfBanned(uid, chat_id)
        or (
            await get_silence(chat_id)
            and u_acc not in await get_silence_allowed(chat_id)
        )
        or await getUChatLimit(
            message.date, await get_user_last_message(uid, chat_id, 0), u_acc, chat_id
        )
    ):
        return False
    print(214)

    if cmd in settings.commands.lvlbanned and await getULvlBanned(uid):
        await messagereply(message, await messages.lvlbanned())
        return False
    print(215)

    chat_settings = await get_chat_settings(chat_id)
    if chat_settings["main"]["captcha"]:
        async with (await pool()).acquire() as conn:
            if await conn.fetchval(
                "select exists(select id from typequeue where chat_id=$1 and uid=$2 and type='captcha')",
                chat_id,
                uid,
            ):
                return False
    print(216)

    if returncmd:
        return cmd
    return True
