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
from Bot.checkers import getUChatLimit
from Bot.utils import getUserLastMessage, getUserAccessLevel, getUserMute, sendMessage, deleteMessages, \
    getChatSettings, kickUser, getUserName, getUserNickname, antispamChecker, punish, getUserBan, getUserBanInfo, \
    getUserPremium, getIDFromMessage, getUserPremmenuSetting, getChatName, getUserPrefixes, getSilence, \
    getSilenceAllowed, addUserXP
from config.config import PM_COMMANDS, ADMINS, MATHGIVEAWAYS_TO
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
        elif event.object.message.attachments[0].market:
            return await sendMessage(chat_id, messages.pm_market(), kbd=keyboard.pm_market())

    if await answer_handler(event):
        return

    uid = event.object.message.from_id
    msgtime = event.object.message.date
    chat_id = event.object.message.peer_id - 2000000000
    if uid in ADMINS:
        print(f'{uid}({chat_id}): {msg}')

    async with (await pool()).acquire() as conn:
        await conn.execute('insert into allusers (uid) values ($1) on conflict (uid) do nothing', uid)
        await conn.execute('insert into allchats (chat_id) values ($1) on conflict (chat_id) do nothing', chat_id)

        if await conn.fetchval('select exists(select 1 from filters where chat_id=$1 and filter=ANY($2))',
                               chat_id, msg.lower().split()) and not await getUserAccessLevel(uid, chat_id):
            return await deleteMessages(event.object.message.conversation_message_id, chat_id)

    data = event.object.message.text.split()
    if not any(event.object.message.text.startswith(i) for i in await getUserPrefixes(
            await getUserPremium(uid), uid)) and (pinged := [i for i in [
                await getIDFromMessage(event.object.message.text, None, place=k) for k in range(
            1, len(data) + 1) if not data[k - 1].isdigit()] if i]):
        async with (await pool()).acquire() as conn:
            if (await conn.fetchval('select exists(select 1 from antitag where chat_id=$1)', chat_id) and
                    await conn.fetchval('select exists(select 1 from antitag where chat_id=$1 and uid=ANY($2))',
                                        chat_id, pinged) and
                    await deleteMessages(event.object.message.conversation_message_id, chat_id)):
                return await sendMessage(event.object.message.peer_id, messages.antitag_on(
                    uid, await getUserNickname(uid, chat_id), await getUserName(uid)))
        if tonotif := [i for i in pinged if await getUserPremmenuSetting(i, 'tagnotif', False)]:
            for i in tonotif:
                if not await sendMessage(
                        i, f'💥 [id{i}|{await getUserName(i)}], вас тегнул [id{uid}|{await getUserName(uid)}] '
                           f'в чате ({await getChatName(chat_id)}) с текстом: "{event.object.message.text}"'):
                    async with (await pool()).acquire() as conn:
                        await conn.execute(
                            'update premmenu set pos = $1 where uid=$2 and setting=$3', 0, uid, 'tagnotif')

    if (ban := await getUserBan(uid, chat_id)) >= time.time():
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
        await sendMessage(event.object.message.peer_id, messages.kick_banned(
            uid, await getUserName(uid), await getUserNickname(uid, chat_id), ban,
            (await getUserBanInfo(uid, chat_id))['causes'][-1]))
        return await kickUser(uid, chat_id=chat_id)
    if (uacc := await getUserAccessLevel(uid, chat_id)) == 0 and await getUChatLimit(
            msgtime, await getUserLastMessage(uid, chat_id, 0), uacc, chat_id):
        return await deleteMessages(event.object.message.conversation_message_id, chat_id)
    if ((await getSilence(chat_id) and uacc not in await getSilenceAllowed(chat_id)) or
            await getUserMute(uid, chat_id) > int(msgtime)):
        return await deleteMessages(event.object.message.conversation_message_id, chat_id)
    settings = await getChatSettings(chat_id)
    if uacc == 0 and settings['main']['disallowPings'] and any(
            i in ['@all', '@online', '@everyone', '@here', '@все', '@тут', '@здесь', '@онлайн'] for i in
            event.object.message.text.replace('*', '@').lower().split()):
        return await deleteMessages(event.object.message.conversation_message_id, chat_id)
    if settings['main']['nightmode'] and uacc < 6:
        async with (await pool()).acquire() as conn:
            chatsetting = await conn.fetchrow(
                'select value2 from settings where chat_id=$1 and setting=\'nightmode\'', chat_id)
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
            if settings['main']['disallowStickers']:
                return await deleteMessages(event.object.message.conversation_message_id, chat_id)
            sticker = True
        else:
            sticker = False
    except:
        sticker = False

    if settings['antispam']['messagesPerMinute']:
        async with (await pool()).acquire() as conn:
            if (setting := await conn.fetchval(
                'select "value" from settings where chat_id=$1 and setting=\'messagesPerMinute\'', chat_id)
                ) and await conn.fetchval('select count(*) as c from antispammessages where chat_id=$1 and from_id=$2',
                                          chat_id, uid) < setting:
                await conn.execute(
                    'insert into antispammessages (cmid, chat_id, from_id, time) values ($1, $2, $3, $4)',
                    event.object.message.conversation_message_id, chat_id, uid, event.object.message.date)

    if uacc < 5 and (setting := await antispamChecker(chat_id, uid, event.object.message, settings)):
        async with (await pool()).acquire() as conn:
            setting = await conn.fetchrow(
                'select id, setting, "value" from settings where chat_id=$1 and setting=$2', chat_id, setting)
        if punishment := await punish(uid, chat_id, setting[0]):
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            if punishment != 'del':
                await sendMessage(chat_id + 2000000000, messages.antispam_punishment(
                    uid, await getUserName(uid), await getUserNickname(uid, chat_id), setting[1], punishment[0],
                    setting[2], punishment[1] if len(punishment) > 1 else None))

    if chat_id == MATHGIVEAWAYS_TO and msg.replace('-', '').isdigit():
        async with (await pool()).acquire() as conn:
            math = await conn.fetchrow(
                'select id, cmid, ans, xp, math from mathgiveaway where finished=false order by id desc')
            if math[2] == int(msg):
                await conn.execute('update mathgiveaway set winner=$1, finished=true where id=$2', uid, math[0])
                await addUserXP(uid, math[3])
                await deleteMessages(math[1], MATHGIVEAWAYS_TO)
                await sendMessage(MATHGIVEAWAYS_TO + 2000000000, messages.math_winner(
                    uid, await getUserName(uid), await getUserNickname(uid, MATHGIVEAWAYS_TO), msg, math[3], math[4]))
    await add_msg_counter(chat_id, uid, audio, sticker)
