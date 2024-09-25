import time
from ast import literal_eval
from datetime import datetime

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserAccessLevel, getUserName, getUserNickname, kickUser, getUserBan, \
    setChatMute, getUserWarns
from config.config import API
from db import GPool, Ban, Mute, Warn, Nickname

bl = BotLabeler()


@bl.chat_message(SearchCMD('gkick'))
async def gkick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        msg = messages.kick_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.gkick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc >= u_acc:
        msg = messages.kick_higher()
        await message.reply(disable_mentions=1, message=msg)
        return
    data = message.text.split()
    if message.reply_message is None:
        kick_cause = ' '.join(data[2:])
    else:
        kick_cause = ' '.join(data[1:])
    if len(kick_cause) == 0:
        kick_cause = 'Причина не указана'

    try:
        pool = GPool.select().where(GPool.uid == GPool.get(GPool.chat_id == chat_id).uid).iterator()
        pool = [i.chat_id for i in pool]
        if len(pool) == 0:
            raise
    except:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_name = await getUserName(id)
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)
    msg = messages.gkick_start(uid, u_name, u_nickname, id, ch_name, ch_nickname, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('gkick', chat_id, u_acc):
            continue
        try:
            kr = await kickUser(id, chat_id)
            if kr == 1:
                u_nick = await getUserNickname(uid, chat_id)
                ch_nick = await getUserNickname(id, chat_id)
                msg = messages.kick(u_name, u_nick, uid, ch_name, ch_nick, id, kick_cause)
                await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
                success += 1
        except:
            pass

    msg = messages.gkick(id, ch_name, ch_nickname, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gban'))
async def gban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        msg = messages.ban_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.gban_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    if message.reply_message is None:
        if len(data) == 2:
            ban_time = 365 * 86400
            ban_cause = None
        else:
            if data[2].isdigit():
                ban_time = int(data[2]) * 86400
                if ban_time > 86400 * 3650:
                    msg = messages.ban_maxtime()
                    await message.reply(disable_mentions=1, message=msg)
                    return
                ban_cause = None if len(data) == 3 else ' '.join(data[3:])
            else:
                ban_time = 365 * 86400
                ban_cause = ' '.join(data[2:])
    else:
        if len(data) == 1:
            ban_time = 365 * 86400
            ban_cause = None
        else:
            if data[1].isdigit():
                ban_time = int(data[1]) * 86400
                if ban_time > 86400 * 3650:
                    msg = messages.ban_maxtime()
                    await message.reply(disable_mentions=1, message=msg)
                    return
                ban_cause = None if len(data) == 2 else ' '.join(data[2:])
            else:
                ban_time = 365 * 86400
                ban_cause = ' '.join(data[1:])

    banning_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)

    if banning_acc >= u_acc:
        msg = messages.ban_higher()
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
    u_nick = await getUserNickname(uid, chat_id)
    ch_name = await getUserName(id)
    ch_nick = await getUserNickname(id, chat_id)
    msg = messages.gban_start(uid, u_name, u_nick, id, ch_name, ch_nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('gban', chat_id, u_acc):
            continue

        ban_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        res = Ban.get_or_none(Ban.chat_id == chat_id, Ban.uid == id)
        if res is not None:
            ban_times = literal_eval(res.last_bans_times)
            ban_causes = literal_eval(res.last_bans_causes)
            ban_names = literal_eval(res.last_bans_names)
            ban_dates = literal_eval(res.last_bans_dates)
        else:
            ban_times = []
            ban_causes = []
            ban_names = []
            ban_dates = []
        if ban_cause is None:
            ban_cause = 'Без указания причины'
        if ban_date is None:
            ban_date = 'Дата неизвестна'
        ban_times.append(ban_time)
        ban_causes.append(ban_cause)
        ban_names.append(f'[id{uid}|{u_name}]')
        ban_dates.append(ban_date)

        b = Ban.get_or_create(uid=id, chat_id=chat_id)[0]
        b.ban = int(time.time()) + ban_time
        b.last_bans_times = f"{ban_times}"
        b.last_bans_causes = f"{ban_causes}"
        b.last_bans_names = f"{ban_names}"
        b.last_bans_dates = f"{ban_dates}"
        b.save()

        u_nickname = await getUserNickname(uid, chat_id)
        ch_nickname = await getUserNickname(id, chat_id)
        msg = messages.ban(uid, u_name, u_nickname, id, ch_name, ch_nickname, ban_cause, ban_time // 86400)
        kick = await kickUser(id, chat_id)
        if kick:
            await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
        success += 1

    msg = messages.gban(id, ch_name, ch_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gunban'))
async def gunban(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        msg = messages.unban_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.gunban_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
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
    u_nick = await getUserNickname(uid, chat_id)
    nick = await getUserNickname(id, chat_id)
    msg = messages.gunban_start(uid, u_name, u_nick, id, name, nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('gunban', chat_id, u_acc):
            continue
        ch_ban = await getUserBan(id, chat_id)
        if ch_ban > time.time():
            b = Ban.get_or_none(Ban.uid == id, Ban.chat_id == chat_id)
            if b is not None:
                b.delete_instance()
                success += 1

    msg = messages.gunban(id, name, nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gmute'))
async def gmute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        msg = messages.mute_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.gmute_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        if message.reply_message is None:
            mute_time = int(data[2]) * 60
        else:
            mute_time = int(data[1]) * 60
    except:
        mute_time = 0

    if message.reply_message is None:
        mute_cause = ' '.join(data[3:])
    else:
        mute_cause = ' '.join(data[2:])

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc >= u_acc:
        msg = messages.mute_higher()
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
    ch_name = await getUserName(id)
    u_nick = await getUserNickname(uid, chat_id)
    ch_nick = await getUserNickname(uid, chat_id)
    msg = messages.gmute_start(uid, u_name, u_nick, id, ch_name, ch_nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('gmute', chat_id, u_acc):
            continue

        res = Mute.get_or_none(Mute.uid == id, Mute.chat_id == chat_id)
        if res is not None:
            mute_times = literal_eval(res.last_mutes_times)
            mute_causes = literal_eval(res.last_mutes_causes)
            mute_names = literal_eval(res.last_mutes_names)
            mute_dates = literal_eval(res.last_mutes_dates)
        else:
            mute_times = []
            mute_causes = []
            mute_names = []
            mute_dates = []

        mute_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        if mute_cause is None:
            mute_cause = 'Без указания причины'
        if mute_date is None:
            mute_date = 'Дата неизвестна'

        mute_times.append(mute_time)
        mute_causes.append(mute_cause)
        mute_names.append(f'[id{uid}|{u_name}]')
        mute_dates.append(mute_date)

        ms = Mute.get_or_create(uid=id, chat_id=chat_id)[0]
        ms.mute = int(time.time()) + mute_time
        ms.last_mutes_times = f"{mute_times}"
        ms.last_mutes_causes = f"{mute_causes}"
        ms.last_mutes_names = f"{mute_names}"
        ms.last_mutes_dates = f"{mute_dates}"
        ms.save()

        await setChatMute(id, chat_id, mute_time)
        msg = messages.mute(u_name, u_nick, uid, ch_name, ch_nick, id, mute_cause, int(mute_time / 60))

        await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
        success += 1

    msg = messages.gmute(id, ch_name, ch_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gunmute'))
async def gunmute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        msg = messages.unmute_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.gunmute_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc >= u_acc:
        msg = messages.unmute_higher()
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
    ch_name = await getUserName(id)
    u_nick = await getUserNickname(uid, chat_id)
    ch_nick = await getUserNickname(id, chat_id)
    msg = messages.gunmute_start(uid, u_name, u_nick, id, ch_name, ch_nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('gunmute', chat_id, u_acc):
            continue
        m = Mute.get_or_none(Mute.uid == id, Mute.chat_id == chat_id)
        if m is not None and m.mute > time.time():
            m.mute = 0
            m.save()
            await setChatMute(id, chat_id, 0)

            u_nickname = await getUserNickname(uid, chat_id)
            ch_nickname = await getUserNickname(id, chat_id)
            msg = messages.unmute(u_name, u_nickname, uid, ch_name, ch_nickname, id)
            await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
        success += 1

    msg = messages.gunmute(id, ch_name, ch_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gwarn'))
async def gwarn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        msg = messages.warn_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.gwarn_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc >= u_acc:
        msg = messages.unmute_higher()
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

    if message.reply_message is None:
        warn_cause = ' '.join(data[2:])
    else:
        warn_cause = ' '.join(data[1:])

    u_name = await getUserName(uid)
    ch_name = await getUserName(id)
    u_nick = await getUserNickname(uid, chat_id)
    ch_nick = await getUserNickname(id, chat_id)
    msg = messages.gwarn_start(uid, u_name, u_nick, id, ch_name, ch_nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('gwarn', chat_id, u_acc):
            continue

        warn_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        res = Warn.get_or_none(Warn.chat_id == chat_id, Warn.uid == id)
        if res is not None:
            warns = res.warns + 1
            warn_times = literal_eval(res.last_warns_times)
            warn_causes = literal_eval(res.last_warns_causes)
            warn_names = literal_eval(res.last_warns_names)
            warn_dates = literal_eval(res.last_warns_dates)
        else:
            warns = 1
            warn_times = []
            warn_causes = []
            warn_names = []
            warn_dates = []
        if warn_cause is None:
            warn_cause = 'Без указания причины'
        if warn_date is None:
            warn_date = 'Дата неизвестна'
        warn_times.append(0)
        warn_causes.append(warn_cause)
        warn_names.append(f'[id{uid}|{u_name}]')
        warn_dates.append(warn_date)

        u_nickname = await getUserNickname(uid, chat_id)
        ch_nickname = await getUserNickname(id, chat_id)
        if warns >= 3:
            warns = 0
            await kickUser(id, chat_id)
            msg = messages.warn_kick(u_name, u_nickname, uid, ch_name, ch_nickname, id, warn_cause)
        else:
            msg = messages.warn(u_name, u_nickname, uid, ch_name, ch_nickname, id, warn_cause)
        w = Warn.get_or_create(chat_id=chat_id, uid=id)[0]
        w.warns = warns
        w.last_warns_times = f"{warn_times}"
        w.last_warns_causes = f"{warn_causes}"
        w.last_warns_names = f"{warn_names}"
        w.last_warns_dates = f"{warn_dates}"
        w.save()

        await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
        success += 1

    msg = messages.gwarn(id, ch_name, ch_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gunwarn'))
async def gunwarn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if id == uid:
        msg = messages.unwarn_myself()
        await message.reply(disable_mentions=1, message=msg)
        return
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.gunwarn_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
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
    ch_name = await getUserName(id)
    u_nick = await getUserNickname(uid, chat_id)
    ch_nick = await getUserNickname(id, chat_id)
    msg = messages.gunwarn_start(uid, u_name, u_nick, id, ch_name, ch_nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('gunwarn', chat_id, u_acc):
            continue
        ch_warns = await getUserWarns(id, chat_id)
        if ch_warns == 0:
            continue
        w = Warn.get_or_none(Warn.chat_id == chat_id, Warn.uid == id)
        if w is not None:
            w.warn = ch_warns - 1
            w.save()
            if w.warn == 0:
                w.delete_instance()
            u_nickname = await getUserNickname(uid, chat_id)
            ch_nickname = await getUserNickname(id, chat_id)
            msg = messages.unwarn(u_name, u_nickname, uid, ch_name, ch_nickname, id)
            await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
            success += 1

    msg = messages.gunwarn(id, ch_name, ch_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gsnick'))
async def gsnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.gsnick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    if message.reply_message is None:
        nickname = ' '.join(data[2:])
    else:
        nickname = ' '.join(data[1:])

    if len(nickname) > 46 or '[' in nickname or ']' in nickname:
        msg = messages.snick_too_long_nickname()
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
    ch_name = await getUserName(id)
    u_nick = await getUserNickname(uid, chat_id)
    ch_nick = await getUserNickname(id, chat_id)
    msg = messages.gsnick_start(uid, u_name, u_nick, id, ch_name, ch_nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('gsnick', chat_id, u_acc):
            continue

        u_nickname = await getUserNickname(uid, chat_id)
        ch_nickname = await getUserNickname(id, chat_id)

        n = Nickname.get_or_create(uid=id, chat_id=chat_id)[0]
        n.nickname = nickname
        n.save()

        msg = messages.snick(uid, u_name, u_nickname, id, ch_name, ch_nickname, nickname)
        await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
        success += 1

    msg = messages.gsnick(id, ch_name, ch_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('grnick'))
async def grnick(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if (len(data) == 1 and message.reply_message is None) or not id:
        msg = messages.grnick_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
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
    ch_name = await getUserName(id)
    u_nick = await getUserNickname(uid, chat_id)
    ch_nick = await getUserNickname(id, chat_id)
    msg = messages.grnick_start(uid, u_name, u_nick, id, ch_name, ch_nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        ch_acc = await getUserAccessLevel(id, chat_id)
        ch_nickname = await getUserNickname(id, chat_id)
        if u_acc <= ch_acc or not await haveAccess('grnick', chat_id, u_acc) or ch_nickname is None:
            continue
        n = Nickname.get_or_none(Nickname.uid == id, Nickname.chat_id == chat_id)
        if n is not None:
            n.delete_instance()
        u_nickname = await getUserNickname(uid, chat_id)
        msg = messages.rnick(uid, u_name, u_nickname, id, ch_name, ch_nickname)
        await API.messages.send(disable_mentions=1, random_id=0, message=msg, chat_id=chat_id)
        success += 1

    msg = messages.grnick(id, ch_name, ch_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)


@bl.chat_message(SearchCMD('gzov'))
async def gzov(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.gzov_hint()
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
    u_nick = await getUserNickname(uid, chat_id)
    msg = messages.gzov_start(uid, u_name, u_nick, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    success = 0
    cause = ' '.join(data[1:])
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('gzov', chat_id, u_acc):
            continue
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        u_name = await getUserName(uid)
        u_nickname = await getUserNickname(uid, chat_id)
        msg = messages.zov(uid, u_name, u_nickname, cause, members)
        await API.messages.send(random_id=0, message=msg, chat_id=chat_id)
        success += 1

    msg = messages.gzov(uid, u_name, u_nick, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.conversation_message_id, message=msg)
