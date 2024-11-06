import time
from datetime import datetime

from vkbottle_types.events.bot_events import MessageNew
from vkbottle_types.objects import MessagesMessageAttachmentType

import keyboard
import messages
from Bot.action_handlers import action_handle
from Bot.add_msg_count import add_msg_counter
from Bot.answers_handlers import answer_handler
from Bot.checkers import getUChatLimit, getSilence
from Bot.utils import getUserLastMessage, getUserAccessLevel, getUserMute, addDailyTask, sendMessage, deleteMessages, \
    getChatSettings, kickUser, getUserName, getUserNickname, antispamChecker, punish, getUserBan, getUserBanInfo
from config.config import ADMINS, PM_COMMANDS
from db import pool


async def message_handle(event: MessageNew) -> None:
    timestart = datetime.now()
    if event.object.message.action:
        await action_handle(event)
        return
    msg = event.object.message.text
    if event.object.message.peer_id < 2000000000:
        chat_id = event.object.message.peer_id
        for i in PM_COMMANDS:
            if i in msg:
                return
        if len(event.object.message.attachments) == 0:
            msg = messages.pm()
            await sendMessage(chat_id, msg)
            return
        elif event.object.message.attachments[0].market is not None:
            msg = messages.pm_market()
            await sendMessage(chat_id, msg, kbd=keyboard.pm_market())
            return

    if await answer_handler(event) is not False:
        return

    uid = event.object.message.from_id
    msgtime = event.object.message.date
    chat_id = event.object.message.peer_id - 2000000000
    if uid in ADMINS:
        print(f'{uid}({chat_id}): {msg}')

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into allusers (uid) values (%s) on conflict (uid) do nothing', (uid,))
            await c.execute('insert into allchats (chat_id) values (%s) on conflict (chat_id) do nothing', (chat_id,))
            await conn.commit()
            
            if await (await c.execute('select id from filters where chat_id=%s and filter=ANY(%s)',
                                      (chat_id, [i.lower() for i in msg.lower().split()]))).fetchone():
                await deleteMessages(event.object.message.conversation_message_id, chat_id)
                return

    ban = await getUserBan(uid, chat_id)
    if ban >= time.time():
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
        await sendMessage(event.object.message.peer_id, messages.kick_banned(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), ban,
            (await getUserBanInfo(uid, chat_id))['causes'][-1]))
        await kickUser(uid, chat_id=chat_id)
        return
    uacc = await getUserAccessLevel(uid, chat_id)
    if uacc == 0 and await getUChatLimit(msgtime, await getUserLastMessage(uid, chat_id, 0), uacc, chat_id):
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
        return
    settings = await getChatSettings(chat_id)
    if await getUserMute(uid, chat_id) > int(msgtime):
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
        if settings['main']['kickBlockingViolator']:
            if await kickUser(uid, chat_id):
                await sendMessage(event.object.message.peer_id,
                                  messages.kicked(uid, await getUserName(uid), await getUserNickname(uid, chat_id)))
        return
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
                await deleteMessages(event.object.message.conversation_message_id, chat_id)
                return

    if uacc == 0 and await getSilence(chat_id):
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
        return

    try:
        if event.object.message.attachments[0].type == MessagesMessageAttachmentType.AUDIO_MESSAGE:
            audio = True
        else:
            audio = False
    except:
        audio = False

    try:
        if event.object.message.attachments[0].sticker.sticker_id:
            await addDailyTask(uid, 'stickers')
    except:
        pass

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
            name = await getUserName(uid)
            nick = await getUserNickname(uid, chat_id)
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            await sendMessage(chat_id + 2000000000, messages.antispam_punishment(
                uid, name, nick, setting[1], punishment[0], setting[2], punishment[1] if len(punishment) > 1 else None))

    await add_msg_counter(chat_id, uid, audio)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute(
                'insert into messagesstatistics (timestart, timeend) values (%s, %s)', (timestart, datetime.now()))
            await conn.commit()
