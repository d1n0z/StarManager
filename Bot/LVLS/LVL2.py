import time

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.rules import SearchCMD
from Bot.utils import getIDFromMessage, getUserAccessLevel, getUserNickname, getUserMute, getUserName, setChatMute, \
    getChatAccessName, setUserAccessLevel
from config.config import MAIN_DEVS, DEVS
from db import pool

bl = BotLabeler()


@bl.chat_message(SearchCMD('unmute'))
async def unmute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.unmute_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())

    if await getUserAccessLevel(id, chat_id) >= await getUserAccessLevel(uid, chat_id):
        return await message.reply(disable_mentions=1, message=messages.unmute_higher())

    if await getUserMute(id, chat_id) <= time.time():
        return await message.reply(disable_mentions=1, message=messages.unmute_no_mute(
            id, await getUserName(id), await getUserNickname(id, chat_id)))

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('update mute set mute = 0 where chat_id=%s and uid=%s', (chat_id, id))
            await conn.commit()

    await setChatMute(id, chat_id, 0)
    await message.reply(disable_mentions=1, message=messages.unmute(
        await getUserName(uid), await getUserNickname(uid, chat_id), uid, await getUserName(id),
        await getUserNickname(id, chat_id), id))


@bl.chat_message(SearchCMD('mutelist'))
async def mutelist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_mutes_causes, mute, last_mutes_names from mute where chat_id=%s and '
                'mute>%s order by uid desc', (message.peer_id - 2000000000, int(time.time())))).fetchall()
    muted_count = len(res)
    await message.reply(disable_mentions=1, message=await messages.mutelist(res[:30], muted_count),
                        keyboard=keyboard.mutelist(message.from_id, 0, muted_count))


@bl.chat_message(SearchCMD('unwarn'))
async def unwarn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.unwarn_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if id == uid:
        return await message.reply(disable_mentions=1, message=messages.unwarn_myself())

    if await getUserAccessLevel(id, chat_id) >= await getUserAccessLevel(uid, chat_id):
        return await message.reply(disable_mentions=1, message=messages.unwarn_higher())

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute(
                    'update warn set warns = warns - 1 where chat_id=%s and uid=%s', (chat_id, id))).rowcount:
                msg = messages.unwarn_no_warns(id, await getUserName(id), await getUserNickname(id, chat_id))
                await message.reply(disable_mentions=1, message=msg)
                return
            await conn.commit()
    await message.reply(disable_mentions=1, message=messages.unwarn(
        await getUserName(uid), await getUserNickname(uid, chat_id), uid, await getUserName(id),
        await getUserNickname(id, chat_id), id))


@bl.chat_message(SearchCMD('warnlist'))
async def warnlist(message: Message):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_warns_causes, warns, last_warns_names from warn where chat_id=%s and '
                'warns>0 order by uid desc', (message.peer_id - 2000000000,))).fetchall()
    count = len(res)
    res = res[:30]
    await message.reply(disable_mentions=1, message=await messages.warnlist(res, count), keyboard=keyboard.warnlist(
        message.from_id, 0, count))


@bl.chat_message(SearchCMD('setaccess'))
async def setaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id or (len(data) + bool(message.reply_message) < 3) or not data[-1].isdigit():
        return await message.reply(disable_mentions=1, message=messages.setacc_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if id == uid and uid not in MAIN_DEVS:
        return await message.reply(disable_mentions=1, message=messages.setaccess_myself())

    acc = int(data[-1])
    if not (0 < acc < 7) and uid not in MAIN_DEVS:
        return await message.reply(disable_mentions=1, message=messages.setacc_hint())
    ch_acc = await getUserAccessLevel(id, chat_id)
    if acc == ch_acc:
        return await message.reply(disable_mentions=1, message=messages.setacc_already_have_acc(
            id, await getUserName(id), ch_acc))

    u_acc = await getUserAccessLevel(uid, chat_id)
    if not (acc < u_acc or u_acc >= 8) and uid not in MAIN_DEVS:
        return await message.reply(disable_mentions=1, message=messages.setacc_low_acc(acc))
    if ch_acc >= u_acc and uid not in MAIN_DEVS:
        return await message.reply(disable_mentions=1, message=messages.setacc_higher())

    await setUserAccessLevel(id, chat_id, acc)
    await message.reply(disable_mentions=1, message=messages.setacc(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), acc, id, await getUserName(id),
        await getUserNickname(id, chat_id), await getChatAccessName(chat_id, acc)))


@bl.chat_message(SearchCMD('delaccess'))
async def delaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await getIDFromMessage(message.text, message.reply_message)
    if not id:
        return await message.reply(disable_mentions=1, message=messages.delaccess_hint())
    if id < 0:
        return await message.reply(disable_mentions=1, message=messages.id_group())
    if id == uid and uid not in DEVS:
        return await message.reply(disable_mentions=1, message=messages.delaccess_myself())

    ch_acc = await getUserAccessLevel(id, chat_id)
    if ch_acc <= 0:
        return await message.reply(disable_mentions=1, message=messages.delaccess_noacc(
            id, await getUserName(id), await getUserNickname(id, chat_id)))
    if ch_acc >= await getUserAccessLevel(uid, chat_id) and uid not in DEVS:
        return await message.reply(disable_mentions=1, message=messages.delaccess_higher())
    await setUserAccessLevel(id, chat_id, 0)
    await message.reply(disable_mentions=1, message=messages.delaccess(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), id, await getUserName(id),
        await getUserNickname(id, chat_id)))
