import time
from datetime import datetime
from typing import Any

from vkbottle_types.events.bot_events import MessageNew
from vkbottle_types.objects import MessagesMessageAttachmentType

import keyboard
import messages
from Bot.action_handlers import action_handle
from Bot.add_msg_count import add_msg_counter
from Bot.answers_handlers import answer_handler
from Bot.checkers import getUChatLimit, getUserPrefixes
from Bot.utils import getUserLastMessage, getUserAccessLevel, getUserMute, sendMessage, deleteMessages, \
    getChatSettings, kickUser, getUserName, getUserNickname, antispamChecker, punish, getUserBan, getUserBanInfo, \
    getUserPremium, getIDFromMessage, getUserPremmenuSetting, getChatName
from config.config import ADMINS, PM_COMMANDS
from db import pool


async def message_handle(event: MessageNew) -> Any:
    if event.object.message.from_id < 0:
        return
    if event.object.message.action:
        return await action_handle(event)
    msg = event.object.message.text
    if event.object.message.peer_id < 2000000000:
        chat_id = event.object.message.peer_id
        for i in PM_COMMANDS:
            if i in msg:
                return
        if len(event.object.message.attachments) == 0:
            return await sendMessage(chat_id, messages.pm())
        elif event.object.message.attachments[0].market is not None:
            return await sendMessage(chat_id, messages.pm_market(), kbd=keyboard.pm_market())

    if await answer_handler(event):
        return

    uid = event.object.message.from_id
    msgtime = event.object.message.date
    chat_id = event.object.message.peer_id - 2000000000
    if uid in ADMINS:
        print(f'{uid}({chat_id}): {msg}')

    async with ((await pool()).connection() as conn):
        async with conn.cursor() as c:
            await c.execute('insert into allusers (uid) values (%s) on conflict (uid) do nothing', (uid,))
            await c.execute('insert into allchats (chat_id) values (%s) on conflict (chat_id) do nothing', (chat_id,))

            if (await (await c.execute('select id from filters where chat_id=%s and filter=ANY(%s)',
                                       (chat_id, [i.lower() for i in msg.lower().split()]))).fetchone() and
                    not await getUserAccessLevel(uid, chat_id)):
                return await deleteMessages(event.object.message.conversation_message_id, chat_id)

            data = event.object.message.text.split()
            if not any(event.object.message.text.startswith(i) for i in await getUserPrefixes(
                    await getUserPremium(uid), uid)) and (
                    pinged := [i for i in [
                        await getIDFromMessage(event.object.message.text, None, place=k) for k in range(
                            1, len(data) + 1) if not data[k - 1].isdigit()] if i]):
                if (await (await c.execute('select id from antitag where chat_id=%s', (chat_id,))).fetchone() and
                        (await (await c.execute('select id from antitag where chat_id=%s and uid=ANY(%s)',
                                                (chat_id, pinged))).fetchone()) and
                        await deleteMessages(event.object.message.conversation_message_id, chat_id)):
                    return await sendMessage(event.object.message.peer_id, messages.antitag_on(
                        uid, await getUserNickname(uid, chat_id), await getUserName(uid)))
                if tonotif := [i for i in pinged if await getUserPremmenuSetting(i, 'tagnotif', False)]:
                    for i in tonotif:
                        if not await sendMessage(
                                i, f'💥 [id{i}|{await getUserName(i)}], вас тегнул [id{uid}|{await getUserName(uid)}] '
                                   f'в чате ({await getChatName(chat_id)}) с текстом: "{event.object.message.text}"'):
                            await c.execute(
                                'update premmenu set pos = %s where uid=%s and setting=%s', (0, uid, 'tagnotif'))
            await conn.commit()

    if (ban := await getUserBan(uid, chat_id)) >= time.time():
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
        await sendMessage(event.object.message.peer_id, messages.kick_banned(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), ban,
            (await getUserBanInfo(uid, chat_id))['causes'][-1]))
        return await kickUser(uid, chat_id=chat_id)
    if (uacc := await getUserAccessLevel(uid, chat_id)) == 0 and await getUChatLimit(
            msgtime, await getUserLastMessage(uid, chat_id, 0), uacc, chat_id):
        return await deleteMessages(event.object.message.conversation_message_id, chat_id)
    settings = await getChatSettings(chat_id)
    if await getUserMute(uid, chat_id) > int(msgtime):
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
        if settings['main']['kickBlockingViolator']:
            if await kickUser(uid, chat_id):
                await sendMessage(event.object.message.peer_id,
                                  messages.kicked(uid, await getUserName(uid), await getUserNickname(uid, chat_id)))
        return
    if settings['main']['disallowPings'] and any(
            i in ['@all', '@online', '@everyone', '@here', '@все', '@тут', '@здесь', '@онлайн'] for i in
            event.object.message.text.replace('*', '@').lower().split()):
        return await deleteMessages(event.object.message.conversation_message_id, chat_id)
    if settings['main']['nightmode'] and uacc < 6:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
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
                return await deleteMessages(event.object.message.conversation_message_id, chat_id)

    try:
        if event.object.message.attachments[0].type == MessagesMessageAttachmentType.AUDIO_MESSAGE:
            audio = True
        else:
            audio = False
    except:
        audio = False
    try:
        if event.object.message.attachments[0].type == MessagesMessageAttachmentType.STICKER:
            sticker = True
        else:
            sticker = False
    except:
        sticker = False

    if settings['antispam']['messagesPerMinute']:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                uantispammessages = (await (await c.execute(
                    'select count(*) as c from antispammessages where chat_id=%s and from_id=%s',
                    (chat_id, uid))).fetchone())[0]
                setting = await (await c.execute(
                    'select "value" from settings where chat_id=%s and setting=\'messagesPerMinute\'',
                    (chat_id,))).fetchone()
                if setting[0] and uantispammessages < setting[0]:
                    await c.execute(
                        'insert into antispammessages (cmid, chat_id, from_id, time) values (%s, %s, %s, %s)',
                        (event.object.message.conversation_message_id, chat_id, uid, event.object.message.date))
                    await conn.commit()

    if uacc < 5 and (setting := await antispamChecker(chat_id, uid, event.object.message, settings)):
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                setting = await (await c.execute(
                    'select id, setting, "value" from settings where chat_id=%s and setting=%s',
                    (chat_id, setting))).fetchone()
        if punishment := await punish(uid, chat_id, setting[0]):
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            if punishment != 'del':
                await sendMessage(chat_id + 2000000000, messages.antispam_punishment(
                    uid, await getUserName(uid), await getUserNickname(uid, chat_id), setting[1], punishment[0],
                    setting[2], punishment[1] if len(punishment) > 1 else None))

    await add_msg_counter(chat_id, uid, audio, sticker)
