import time

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserName, getUserNickname, getUserAccessLevel, getUserPremium, editMessage
from config.config import API
from db import GPool, AccessLevel, ChatGroups, Ignore, ChatLimit, Notifs, Nickname

bl = BotLabeler()


@bl.chat_message(SearchCMD('gdelaccess'))
async def gdelaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message)
    if not id:
        msg = messages.gdelaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.delaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        pool = GPool.select().where(GPool.uid == GPool.get(GPool.chat_id == chat_id).uid).iterator()
        pool = [i.chat_id for i in pool]
        if len(pool) == 0:
            raise
    except:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(id)
    u_name = await getUserName(uid)
    ch_nickname = await getUserNickname(id, chat_id)
    u_nickname = await getUserNickname(uid, chat_id)

    msg = messages.gdelaccess_start(uid, u_name, u_nickname, id, name, ch_nickname, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)

    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if ch_acc > u_acc or not await haveAccess('gdelaccess', chat_id, u_acc):
            continue

        ac = AccessLevel.get_or_none(AccessLevel.uid == id, AccessLevel.chat_id == chat_id)
        if ac is not None:
            ac.delete_instance()
            success += 1

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.gdelaccess(id, name, nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gsetaccess'))
async def gsetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 2 and message.reply_message is None) or
            (len(data) <= 1 and message.reply_message is not None)):
        msg = messages.gsetaccess_hint()
        await message.reply(message=msg, disable_mentions=1)
        return
    id = await getIDFromMessage(message)
    if not id:
        msg = messages.gsetaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.setaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        acc = int(data[-1])
        if acc <= 0 or acc >= 7:
            raise
    except:
        msg = messages.setacc_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        pool = GPool.select().where(GPool.uid == GPool.get(GPool.chat_id == chat_id).uid).iterator()
        pool = [i.chat_id for i in pool]
        if len(pool) == 0:
            raise
    except:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    u_name = await getUserName(uid)
    name = await getUserName(id)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)

    msg = messages.gsetaccess_start(uid, u_name, u_nickname, id, name, ch_nickname, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)

        if acc >= u_acc or ch_acc >= u_acc or ch_acc >= acc or not await haveAccess('gsetaccess', chat_id, u_acc):
            continue

        ac = AccessLevel.get_or_create(uid=id, chat_id=chat_id)[0]
        ac.access_level = acc
        ac.save()
        success += 1

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.gsetaccess(id, name, nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('demote'))
async def demote(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    msg = messages.demote_choose()
    kb = keyboard.demote_choose(uid, chat_id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('ssetaccess'))
async def ssetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 3 and message.reply_message is None) or
            (len(data) <= 2 and message.reply_message is not None)):
        msg = messages.ssetaccess_hint()
        await message.reply(message=msg, disable_mentions=1)
        return
    id = await getIDFromMessage(message, 3)
    if not id:
        msg = messages.ssetaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.setaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        acc = int(data[-1])
        if acc <= 0 or acc >= 7:
            raise
    except:
        msg = messages.setacc_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        res = AccessLevel.get(AccessLevel.chat_id == chat_id, AccessLevel.access_level > 6)
        pool = ChatGroups.select().where(ChatGroups.group == data[1], ChatGroups.uid == res.uid)
        pool = [i.chat_id for i in pool]
        if len(pool) == 0:
            raise Exception
    except:
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    u_name = await getUserName(uid)
    name = await getUserName(id)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)

    msg = messages.ssetaccess_start(uid, u_name, u_nickname, id, name, ch_nickname, data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if acc >= u_acc or ch_acc >= u_acc or ch_acc >= acc or not await haveAccess('ssetaccess', chat_id, u_acc):
            continue

        ac = AccessLevel.get_or_create(uid=id, chat_id=chat_id)[0]
        ac.access_level = acc
        ac.save()
        success += 1

    ch_nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.ssetaccess(id, name, ch_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('sdelaccess'))
async def sdelaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if ((len(data) <= 2 and message.reply_message is None) or
            (len(data) <= 1 and message.reply_message is not None)):
        msg = messages.sdelaccess_hint()
        await message.reply(message=msg, disable_mentions=1)
        return
    id = await getIDFromMessage(message, 3)
    if not id:
        msg = messages.sdelaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if uid == id:
        msg = messages.delaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        res = AccessLevel.get(AccessLevel.chat_id == chat_id, AccessLevel.access_level > 6)
        pool = ChatGroups.select().where(ChatGroups.group == data[1], ChatGroups.uid == res.uid)
        pool = [i.chat_id for i in pool]
        if len(pool) == 0:
            raise Exception
    except:
        msg = messages.s_invalid_group(data[1])
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(id)
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)

    msg = messages.sdelaccess_start(uid, u_name, u_nickname, id, name, ch_nickname, data[1])
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)

        if ch_acc > u_acc or ch_acc == 0 or not await haveAccess('sdelaccess', chat_id, u_acc):
            continue

        ac = AccessLevel.get_or_none(AccessLevel.uid == id, AccessLevel.chat_id == chat_id)
        if ac is not None:
            ac.delete_instance()
            success += 1

    nick = await getUserNickname(id, edit.peer_id - 2000000000)
    msg = messages.sdelaccess(id, name, nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id,
                            message=msg)


@bl.chat_message(SearchCMD('ignore'))
async def ignore(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    if len(data) != 2:
        msg = messages.ignore_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    id = await getIDFromMessage(message, 3)
    if not id:
        msg = messages.ignore_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(id)
    _ = Ignore.get_or_create(uid=id, chat_id=chat_id)

    nick = await getUserNickname(uid, chat_id)
    msg = messages.ignore(id, name, nick)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('unignore'))
async def unignore(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    if len(data) != 2:
        msg = messages.unignore_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    id = await getIDFromMessage(message, 3)
    if not id:
        msg = messages.ignore_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    name = await getUserName(id)

    ign = Ignore.get_or_none(Ignore.uid == id, Ignore.chat_id == chat_id)
    if ign is None:
        msg = messages.unignore_not_ignored()
        await message.reply(disable_mentions=1, message=msg)
        return
    ign.delete_instance()

    nick = await getUserNickname(uid, chat_id)
    msg = messages.unignore(id, name, nick)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('ignorelist'))
async def ignorelist(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if int(u_prem) <= 0:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    ign = Ignore.select().where(Ignore.chat_id == chat_id)
    ids = []
    for i in ign:
        ids.append(str(i.uid))

    raw_names = await API.users.get(','.join(ids))
    names = []
    for i in raw_names:
        names.append(f'{i.first_name} {i.last_name}')

    msg = messages.ignorelist(ign, names)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('chatlimit'))
async def chatlimit(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_prem = await getUserPremium(uid)
    if not u_prem:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    if len(data) != 2:
        msg = messages.chatlimit_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    t = data[1]
    pfx = t[-1]
    if t != '0':
        if not t[:-1].isdigit() or pfx not in ['s', 'm', 'h']:
            msg = messages.chatlimit_hint()
            await message.reply(disable_mentions=1, message=msg)
            return

        st = int(t[:-1])
        tst = int(st)
        if pfx == 'm':
            st *= 60
        elif pfx == 'h':
            st *= 60 * 60
    else:
        st = 0
        tst = 0

    chlim = ChatLimit.get_or_none(ChatLimit.chat_id == chat_id)
    if chlim is not None:
        lpos = chlim.time
        chlim.time = st
        chlim.save()
    else:
        lpos = 1
        ChatLimit.create(chat_id=chat_id, time=st)

    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)

    msg = messages.chatlimit(uid, name, nick, tst, pfx, lpos)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('resetnick'))
async def resetnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    kb = keyboard.resetnick_accept(uid, chat_id)
    msg = messages.resetnick_yon()
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('resetaccess'))
async def resetaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) != 2 or not data[1].isdigit() or int(data[1]) < 1 or int(data[1]) > 6:
        msg = messages.resetaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    uid = message.from_id
    kb = keyboard.resetaccess_accept(uid, chat_id, data[1])
    msg = messages.resetaccess_yon(data[1])
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('notif'))
async def notif(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) >= 2:
        name = ' '.join(data[1:])
        notif = Notifs.get_or_none(Notifs.name == name)
        if notif is not None:
            msg = messages.notif_already_exist(notif.name)
            await message.reply(disable_mentions=1, message=msg)
            return
        else:
            Notifs.create(chat_id=chat_id, tag=1, every=-1, status=1, time=time.time() - 5,
                          name=name, description='', text='')
            msg = messages.notification(name, '', time.time(), -1, 1, 1)
            kb = keyboard.notification(uid, 1, name)
            await message.reply(disable_mentions=1, message=msg, keyboard=kb)
        return
    activenotifs = [i for i in Notifs.select().where(Notifs.chat_id == chat_id, Notifs.status == 1)]
    notifs = [i for i in Notifs.select().where(Notifs.chat_id == chat_id)]
    msg = messages.notif(notifs, activenotifs)
    kb = keyboard.notif(uid)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('purge'))
async def purge(message: Message):
    chat_id = message.peer_id - 2000000000

    users = [i.member_id for i in (await API.messages.get_conversation_members(message.peer_id)).items]
    dtdnicknames = 0
    dtdaccesslevels = 0
    for i in Nickname.select().where(Nickname.chat_id == chat_id).iterator():
        if i.uid not in users:
            i.delete_instance()
            dtdnicknames += 1
    for i in AccessLevel.select().where(AccessLevel.chat_id == chat_id).iterator():
        if i.uid not in users:
            i.delete_instance()
            dtdaccesslevels += 1

    msg = messages.purge_start()
    edit = await message.reply(disable_mentions=1, message=msg)
    if dtdnicknames > 0 or dtdaccesslevels > 0:
        msg = messages.purge(dtdnicknames, dtdaccesslevels)
    else:
        msg = messages.purge_empty()
    await editMessage(msg, message.peer_id, edit.conversation_message_id)
