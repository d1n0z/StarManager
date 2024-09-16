import threading
import traceback

import messages
from Bot.global_warn_handler import global_warn_handle
from Bot.utils import getUserAccessLevel, getUserPremium, getUserLastMessage, getUserMute
from config.config import COMMANDS, API, PREFIX, DEVS, MAIN_DEVS, LVL_BANNED_COMMANDS
from db import GlobalWarns, CMDLevels, Prefixes, Ignore, InfBanned, SilenceMode, ChatLimit, CMDNames, LvlBanned


async def isAdmin(cmd, chat_id) -> bool:
    if cmd not in COMMANDS:
        return True
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
    inf = InfBanned.get_or_none(InfBanned.type == 'group', InfBanned.uid == chat_id)
    if inf is not None:
        return 0
    inf = InfBanned.get_or_none(InfBanned.type == 'user', InfBanned.uid == uid)
    if inf is not None:
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
    elif text[:2] in PREFIX:
        prefix = text[:2]
    else:
        prefix = Prefixes.get_or_none(Prefixes.uid == uid, Prefixes.prefix << [text[:1], text[:2]])
        if prefix is None:
            return False
        prefix = prefix.prefix

    if text.replace(prefix, '') in COMMANDS:
        cmd = text.replace(prefix, '')
    else:
        cmd = CMDNames.get_or_none(CMDNames.uid == uid, CMDNames.name == text.replace(prefix, ''))
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

    admin = await isAdmin(cmd, chat_id)
    if not admin:
        msg = messages.notadmin()
        try:
            await message.reply(msg)
        except:
            await API.messages.send(message=message, random_id=0, chat_id=chat_id)
        return False

    u_prem = await getUserPremium(uid)
    u_acc = await getUserAccessLevel(uid, chat_id)
    access = await haveAccess(cmd, chat_id, u_acc, await getUserPremium(uid))
    uprefixes = await getUserPrefixes(u_prem, uid)
    ign = await getUserIgnore(uid, chat_id)
    infb = await getUInfBanned(uid, chat_id)
    lm = await getUserLastMessage(uid, chat_id, 0)
    chlim = await getUChatLimit(message.date, lm, u_acc, chat_id)
    mute = await getUserMute(uid, chat_id)
    timeout = await getSilence(chat_id)

    if chlim or mute > message.date or (timeout and u_acc == 0):
        try:
            await API.messages.delete(cmids=message.conversation_message_id, peer_id=chat_id + 2000000000,
                                      delete_for_all=True)
        except:
            pass

        return False

    if prefix not in uprefixes or not access or ign or not infb:
        return False

    threading.Thread(target=global_warn_handle, args=(uid, cmd,)).start()
    if returncmd:
        return cmd
    return True
