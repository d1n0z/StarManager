import time

from cache.async_ttl import AsyncTTL
from vkbottle.bot import Message

import StarManager.vkbot.messages as messages
from StarManager.core import managers
from StarManager.core.config import settings
from StarManager.core.db import pool
from StarManager.core.utils import (
    command_cooldown_check,
    get_chat_settings,
    get_silence,
    get_silence_allowed,
    get_user_last_message,
    get_user_mute,
    get_user_prefixes,
    get_user_premium,
    messagereply,
)


async def haveAccess(cmd, chat_id, uid, premium=0) -> bool:
    if cmd == "check" and premium:
        return True
    if cmd == "getdev":
        return True

    level = await managers.access_level.get(uid, chat_id)
    custom_level = None

    if level and level.custom_level_name is not None:
        custom_level = await managers.custom_access_level.get(
            level.access_level, chat_id
        )
        if custom_level is not None:
            if not custom_level.status:
                custom_level = None
                level = None

    if level is None or level.custom_level_name is None:
        async with (await pool()).acquire() as conn:
            cmdacc = await conn.fetchval(
                "select lvl from commandlevels where chat_id=$1 and cmd=$2",
                chat_id,
                cmd,
            )
        if cmdacc is not None:
            return cmdacc <= (level.access_level if level else 0)

    if custom_level is not None:
        return cmd in custom_level.commands

    try:
        required = settings.commands.commands[cmd]
        return required <= (level.access_level if level else 0)
    except Exception:
        return 7 <= (level.access_level if level else 0)


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
    return bool(await managers.blocked.get(uid, "user")) or bool(
        await managers.blocked.get(chat_id, "chat")
    )


@AsyncTTL(maxsize=0)
async def getULvlBanned(uid) -> bool:
    if await getUInfBanned(uid, None) or await managers.lvlbanned.exists(uid):
        return True
    return False


async def getUChatLimit(msgtime, get_user_last_message_params, u_acc, chat_id) -> bool:
    if u_acc >= 6:
        return False
    chl = await managers.chatlimit.get(chat_id)
    if not chl:
        return False

    last_message = await get_user_last_message(*get_user_last_message_params)

    if msgtime - last_message >= chl.time:
        return False
    return True


async def checkCMD(
    message: Message, chat_id, fixing=False, accesstoalldevs=False, returncmd=False
) -> bool | str:
    uid = message.from_id
    if message.action is not None:
        return False
    if uid < 0:
        return False
    try:
        text = message.text.lower().split()[0]
    except Exception:
        return False

    prefix = None
    if text[:1] in settings.commands.prefix:
        prefix = text[:1]
    else:
        pv1, pv2 = text[:1], text[:2]
        for p in await managers.prefixes.get_all(uid):
            if pv1 in p or pv2 in p:
                prefix = p
                break
    if not prefix:
        return False

    raw = text.replace(prefix, "", 1)

    if raw in settings.commands.commands:
        cmd = raw
    else:
        db_cmd = await managers.cmdnames.get_or_none(uid, raw)
        if db_cmd:
            cmd = db_cmd
        else:
            if raw in settings.commands.pm and message.peer_id >= 2000000000:
                await messagereply(message, await messages.pmcmd())
            return False

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

    u_acc = await managers.access_level.get(uid, chat_id)
    u_prem = await get_user_premium(uid)
    if (
        not await haveAccess(cmd, chat_id, uid, u_prem)
        or prefix not in await get_user_prefixes(u_prem, uid)
        or await get_user_mute(uid, chat_id) > message.date
        or await getUserIgnore(uid, chat_id)
        or await getUInfBanned(uid, chat_id)
        or (
            await get_silence(chat_id)
            and (u_acc.access_level if u_acc else 0)
            not in await get_silence_allowed(
                chat_id, ((u_acc.custom_level_name is not None) if u_acc else False)
            )
        )
        or await getUChatLimit(
            message.date,
            (uid, chat_id, 0),
            (u_acc.access_level if u_acc else 0),
            chat_id,
        )
    ):
        return False

    if cmd in settings.commands.lvlbanned and await getULvlBanned(uid):
        await messagereply(message, await messages.lvlbanned())
        return False

    chat_settings = await get_chat_settings(chat_id)
    if chat_settings["main"]["captcha"]:
        async with (await pool()).acquire() as conn:
            if await conn.fetchval(
                "select exists(select id from typequeue where chat_id=$1 and uid=$2 and type='captcha')",
                chat_id,
                uid,
            ):
                return False

    if returncmd:
        return cmd
    return True
