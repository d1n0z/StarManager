import traceback
from datetime import datetime

import messages
from Bot.utils import getUserAccessLevel, getUserPremium, getUserLastMessage, getUserMute, getChatSettings, \
    deleteMessages
from config.config import COMMANDS, API, PREFIX, DEVS, MAIN_DEVS, LVL_BANNED_COMMANDS
from db import GlobalWarns, CMDLevels, Prefixes, Ignore, InfBanned, SilenceMode, ChatLimit, CMDNames, LvlBanned, \
    Settings, TypeQueue


async def isAdmin(chat_id) -> bool:
    try:
        await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        return True
    except:
        return False


async def isSGW(uid, msgtime) -> int | bool:
    ugw = GlobalWarns.get_or_none(GlobalWarns.uid == uid)
    if ugw is not None and ugw.time > msgtime:
        return ugw.time
    return False


async def haveAccess(cmd, chat_id, uacc, premium=0) -> int | bool:
    cmdacc = CMDLevels.get_or_none(CMDLevels.chat_id == chat_id, CMDLevels.cmd == cmd)
    if cmd == 'check' and premium:
        return True
    if cmdacc is not None:
        return cmdacc.lvl <= uacc
    try:
        return COMMANDS[cmd] <= uacc
    except:
        traceback.print_exc()
        return 7 <= uacc


async def getUserPrefixes(u_prem, uid) -> list:
    if u_prem:
        return PREFIX + [i.prefix for i in Prefixes.select().where(Prefixes.uid == uid).iterator()]
    return PREFIX


async def getUserIgnore(uid, chat_id) -> int:
    ign = Ignore.get_or_none(Ignore.chat_id == chat_id, Ignore.uid == uid)
    if ign is not None:
        return 1
    return 0


async def getUInfBanned(uid, chat_id) -> int:
    inf = InfBanned.select().where(InfBanned.uid << (chat_id, uid))
    if len(inf):
        return 0
    return 1


async def getULvlBanned(uid) -> int:
    ban = LvlBanned.get_or_none(LvlBanned.uid == uid)
    if ban is not None:
        return 0
    return 1


async def getSilence(chat_id) -> int:
    sm = SilenceMode.get_or_none(SilenceMode.chat_id == chat_id)
    if sm is not None:
        return sm.time
    return 0


async def getUChatLimit(msgtime, last_message, u_acc, chat_id) -> bool:
    chl = ChatLimit.get_or_none(ChatLimit.chat_id == chat_id)
    if chl is not None:
        if chl.time == 0 or msgtime - last_message >= chl.time or u_acc >= 6:
            return False
        return True
    return False


async def checkCMD(message, chat_id, fixing=False, accesstoalldevs=False, returncmd=False) -> bool | str:
    uid = message.from_id
    if uid < 0:
        return False
    try:
        text = message.text.lower().split()[0]
    except:
        return False
    if text[:1] in PREFIX:
        prefix = text[:1]
    else:
        prefix = Prefixes.get_or_none(Prefixes.uid == uid, Prefixes.prefix << [text[:1], text[:2]])
        if prefix is None:
            return False
        prefix = prefix.prefix

    if text.replace(prefix, '', 1) in COMMANDS:
        cmd = text.replace(prefix, '', 1)
    else:
        cmd = CMDNames.get_or_none(CMDNames.uid == uid, CMDNames.name == text.replace(prefix, '', 1))
        if cmd is None:
            return False
        cmd = cmd.cmd

    if cmd in LVL_BANNED_COMMANDS and not await getULvlBanned(uid):
        await message.reply(messages.lvlbanned())
        return False

    accessed = DEVS if accesstoalldevs else MAIN_DEVS
    if fixing and uid not in accessed:
        msg = messages.inprogress()
        await message.reply(disable_mentions=1, message=msg)
        return False

    sgw = await isSGW(uid, message.date)
    if sgw:
        await message.reply(messages.lock(sgw - message.date))
        return False

    u_acc = await getUserAccessLevel(uid, chat_id)
    if ((not await haveAccess(cmd, chat_id, u_acc, await getUserPremium(uid))) or
            (prefix not in await getUserPrefixes(await getUserPremium(uid), uid)) or
            (await getUserMute(uid, chat_id) > message.date) or
            (await getUserIgnore(uid, chat_id)) or
            (not await getUInfBanned(uid, chat_id)) or
            (await getUChatLimit(message.date, await getUserLastMessage(uid, chat_id, 0), u_acc, chat_id)) or
            (await getSilence(chat_id) and u_acc == 0)):
        return False
    settings = await getChatSettings(chat_id)

    if settings['main']['nightmode'] and u_acc < 6:
        chatsetting = Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == 'nightmode')
        if chatsetting is not None:
            if setting := chatsetting.value2:
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
        if TypeQueue.get_or_none(TypeQueue.chat_id == chat_id, TypeQueue.uid == uid,
                                 TypeQueue.type == 'captcha') is not None:
            return False

    if returncmd:
        return cmd
    return True
