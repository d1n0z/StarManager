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
    getChatSettings, kickUser, getUserName, getUserNickname, antispamChecker, punish
from config.config import ADMINS, PM_COMMANDS
from db import AllUsers, AllChats, Filters, AntispamMessages, Settings, MessagesStatistics


async def message_handle(event: MessageNew) -> None:
    dbmsg = MessagesStatistics.create(timestart=datetime.now())
    if event.object.message.action:
        await action_handle(event)
        return
    msg = event.object.message.text
    # MessagesHistory.create(id=event.object.message.id, cmid=event.object.message.conversation_message_id,
    #                        chat_id=chat_id, from_id=uid, text=msg, time=time.time())
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
    AllUsers.get_or_create(uid=uid)
    AllChats.get_or_create(chat_id=chat_id)

    if uid in ADMINS:
        print(f'{uid}({chat_id}): {msg}')

    if Filters.get_or_none(Filters.chat_id == chat_id,
                           Filters.filter << [i.lower() for i in msg.lower().split()]) is not None:
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
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
        userantispammessages = AntispamMessages.select().where(AntispamMessages.from_id == uid,
                                                               AntispamMessages.chat_id == chat_id)
        setting = Settings.get(Settings.chat_id == chat_id, Settings.setting == 'messagesPerMinute')
        if setting.value and len(userantispammessages) < setting.value:
            AntispamMessages.create(cmid=event.object.message.conversation_message_id, chat_id=chat_id, from_id=uid,
                                    time=event.object.message.date)

    if uacc < 5:
        if setting := await antispamChecker(chat_id, uid, event.object.message, settings):
            setting = Settings.get(Settings.chat_id == chat_id, Settings.setting == setting)
            if punishment := await punish(uid, chat_id, setting):
                name = await getUserName(uid)
                nick = await getUserNickname(uid, chat_id)
                await deleteMessages(event.object.message.conversation_message_id, chat_id)
                await sendMessage(chat_id + 2000000000,
                                  messages.antispam_punishment(uid, name, nick, setting.setting,
                                                               punishment[0], setting.value,
                                                               punishment[1] if len(punishment) > 1 else None))

    await add_msg_counter(chat_id, uid, audio)
    dbmsg.timeend = datetime.now()
    dbmsg.save()
