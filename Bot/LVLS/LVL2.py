import time

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserAccessLevel, getUserNickname, getUserMute, getUserName, setChatMute, \
    getChatAccessName, setUserAccessLevel, getSilence, getSilenceAllowed
from config.config import API, MAIN_DEVS, DEVS
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('unmute'))
async def unmute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.unmute_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)
    ch_mute = await getUserMute(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    u_nickname = await getUserNickname(uid, chat_id)
    u_name = await getUserName(uid)
    name = await getUserName(id)

    if ch_acc >= u_acc:
        msg = messages.unmute_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    if ch_mute <= time.time():
        msg = messages.unmute_no_mute(id, name, ch_nickname)
        await message.reply(disable_mentions=1, message=msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('update mute set mute = 0 where chat_id=%s and uid=%s', (chat_id, id))
            await conn.commit()

    await setChatMute(id, chat_id, 0)

    msg = messages.unmute(u_name, u_nickname, uid, name, ch_nickname, id)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('mutelist'))
async def mutelist(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_mutes_causes, mute, last_mutes_names from mute where chat_id=%s and '
                'mute>%s order by uid desc', (chat_id, int(time.time())))).fetchall()
    muted_count = len(res)
    names = await API.users.get(user_ids=[i[0] for i in res[:30]])
    msg = await messages.mutelist(res[:30], names, muted_count)
    kb = keyboard.mutelist(uid, 0, muted_count)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('unwarn'))
async def unwarn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.unwarn_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id == uid:
        msg = messages.unwarn_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    if ch_acc >= u_acc:
        msg = messages.unwarn_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_nickname = await getUserNickname(id, chat_id)
    name = await getUserName(id)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute(
                    'update warn set warns = warns - 1 where chat_id=%s and uid=%s', (chat_id, id))).rowcount:
                msg = messages.unwarn_no_warns(id, name, ch_nickname)
                await message.reply(disable_mentions=1, message=msg)
                return
            await conn.commit()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.unwarn(u_name, u_nickname, uid, name, ch_nickname, id)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('warnlist'))
async def warnlist(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_warns_causes, warns, last_warns_names from warn where chat_id=%s and '
                'warns>0 order by uid desc', (chat_id,))).fetchall()
    count = len(res)
    res = res[:30]
    names = await API.users.get(user_ids=[f'{i[0]}' for i in res])
    msg = await messages.warnlist(res, names, count)
    kb = keyboard.warnlist(uid, 0, count)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('setaccess'))
async def setaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if (not id or (len(data) < 3 and message.reply_message is None) or (
            len(data) < 2 and message.reply_message is not None)):
        msg = messages.setacc_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id == uid and uid not in MAIN_DEVS:
        msg = messages.setaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    try:
        acc = int(data[-1])
    except:
        msg = messages.setacc_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    ch_acc = await getUserAccessLevel(id, chat_id)
    u_name = await getUserName(uid)
    name = await getUserName(id)
    if not (0 < acc < 7):
        msg = messages.setacc_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if acc == ch_acc:
        msg = messages.setacc_already_have_acc(id, name, ch_acc)
        await message.reply(disable_mentions=1, message=msg)
        return

    u_acc = await getUserAccessLevel(uid, chat_id)
    u_nickname = await getUserNickname(uid, chat_id)
    if not (acc < u_acc or u_acc >= 8) and uid not in MAIN_DEVS:
        msg = messages.setacc_low_acc(acc)
        await message.reply(disable_mentions=1, message=msg)
        return
    if ch_acc >= u_acc and uid not in MAIN_DEVS:
        msg = messages.setacc_higher()
        await message.reply(disable_mentions=1, message=msg)
        return

    await setUserAccessLevel(id, chat_id, acc)
    ch_nickname = await getUserNickname(id, chat_id)
    lvlname = await getChatAccessName(chat_id, acc)
    msg = messages.setacc(uid, u_name, u_nickname, acc, id, name, ch_nickname, lvlname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('delaccess'))
async def delaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        msg = messages.delaccess_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id < 0:
        msg = messages.id_group()
        await message.reply(disable_mentions=1, message=msg)
        return
    if id == uid and uid not in DEVS:
        msg = messages.delaccess_myself()
        await message.reply(disable_mentions=1, message=msg)
        return

    ch_acc = await getUserAccessLevel(id, chat_id)
    u_name = await getUserName(uid)
    name = await getUserName(id)
    u_acc = await getUserAccessLevel(uid, chat_id)
    u_nickname = await getUserNickname(uid, chat_id)
    ch_nickname = await getUserNickname(id, chat_id)
    if ch_acc >= u_acc and uid not in DEVS:
        msg = messages.delaccess_higher()
        await message.reply(disable_mentions=1, message=msg)
        return
    if ch_acc <= 0:
        msg = messages.delaccess_noacc(id, name, ch_nickname)
        await message.reply(disable_mentions=1, message=msg)
        return
    await setUserAccessLevel(id, chat_id, 0)
    msg = messages.delaccess(uid, u_name, u_nickname, id, name, ch_nickname)
    await message.reply(disable_mentions=1, message=msg)
