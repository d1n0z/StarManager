import time
from ast import literal_eval
from datetime import datetime

from vkbottle_types.events import MessageNew
from vkbottle_types.objects import MessagesMessageAttachmentType

import keyboard
import messages
from Bot.action_handlers import action_handle
from Bot.add_msg_count import add_msg_counter
from Bot.answers_handlers import answer_handler
from Bot.checkers import getUChatLimit, getSilence
from Bot.utils import getUserLastMessage, getUserAccessLevel, getUserMute, addDailyTask, \
    sendMessage, deleteMessages, getChatSettings, kickUser, getUserName, getUserNickname, antispamChecker, setChatMute
from config.config import ADMINS, PM_COMMANDS
from db import AllUsers, AllChats, Filters, AntispamMessages, Settings, Mute, Ban


async def message_handle(event: MessageNew) -> None:
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
    if await getUChatLimit(msgtime, await getUserLastMessage(uid, chat_id, 0), uacc, chat_id) and uacc == 0:
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
                if not (now.hour < start.hour or now.hour > end.hour or
                        (now.hour == start.hour and now.minute < start.minute) or
                        (now.hour == end.hour and now.minute > end.minute)):
                    await deleteMessages(event.object.message.conversation_message_id, chat_id)
                    return

    if await getSilence(chat_id) and uacc == 0:
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

    if (await getChatSettings(chat_id))['antispam']['messagesPerMinute']:
        userantispammessages = AntispamMessages.select().where(AntispamMessages.from_id == uid,
                                                               AntispamMessages.chat_id == chat_id)
        setting = Settings.get(Settings.chat_id == chat_id, Settings.setting == 'messagesPerMinute')
        if len(userantispammessages) < setting.value:
            AntispamMessages.create(cmid=event.object.message.conversation_message_id, chat_id=chat_id, from_id=uid,
                                    time=event.object.message.date)

    if uacc < 5:
        if setting := await antispamChecker(chat_id, uid, event.object.message, settings):
            print(setting)
            setting = Settings.get(Settings.chat_id == chat_id, Settings.setting == setting)
            print(setting)
            if setting.punishment is None:
                return
            punishment = setting.punishment.split('|')
            print(punishment)
            if punishment[0] == 'deletemessage':
                await deleteMessages(event.object.message.conversation_message_id, chat_id)
                return
            name = await getUserName(uid)
            nick = await getUserNickname(uid, chat_id)
            if punishment[0] == 'kick':
                await deleteMessages(event.object.message.conversation_message_id, chat_id)
                await kickUser(uid, chat_id)
                await sendMessage(chat_id + 2000000000,
                                  messages.antispam_punishment(uid, name, nick, setting.setting, punishment[0],
                                                               setting.value))
            elif punishment[0] == 'mute':
                ms = Mute.get_or_none(Mute.uid == uid, Mute.chat_id == chat_id)
                if ms is not None:
                    mute_times = literal_eval(ms.last_mutes_times)
                    mute_causes = literal_eval(ms.last_mutes_causes)
                    mute_names = literal_eval(ms.last_mutes_names)
                    mute_dates = literal_eval(ms.last_mutes_dates)
                else:
                    mute_times, mute_causes, mute_names, mute_dates = [], [], [], []

                mute_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
                mute_time = int(punishment[1]) * 60
                mute_times.append(mute_time)
                mute_causes.append('Нарушение правил беседы')
                mute_names.append(f'[club222139436|Star Manager]')
                mute_dates.append(mute_date)

                ms = Mute.get_or_create(uid=uid, chat_id=chat_id)[0]
                ms.mute = int(time.time()) + mute_time
                ms.last_mutes_times = f"{mute_times}"
                ms.last_mutes_causes = f"{mute_causes}"
                ms.last_mutes_names = f"{mute_names}"
                ms.last_mutes_dates = f"{mute_dates}"
                ms.save()

                await setChatMute(uid, chat_id, mute_time)
                await deleteMessages(event.object.message.conversation_message_id, chat_id)
                await sendMessage(chat_id + 2000000000,
                                  messages.antispam_punishment(uid, name, nick, setting.setting, punishment[0],
                                                               setting.value, punishment[1]))
            elif punishment[0] == 'ban':
                ban_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
                res = Ban.get_or_none(Ban.chat_id == chat_id, Ban.uid == uid)
                if res is not None:
                    ban_times = literal_eval(res.last_bans_times)
                    ban_causes = literal_eval(res.last_bans_causes)
                    ban_names = literal_eval(res.last_bans_names)
                    ban_dates = literal_eval(res.last_bans_dates)
                else:
                    ban_times, ban_causes, ban_names, ban_dates = [], [], [], []

                ban_cause = 'Нарушение правил беседы'
                ban_time = int(punishment[1]) * 86400
                ban_times.append(ban_time)
                ban_causes.append(ban_cause)
                ban_names.append(f'[club222139436|Star Manager]')
                ban_dates.append(ban_date)

                b = Ban.get_or_create(uid=uid, chat_id=chat_id)[0]
                b.ban = int(time.time()) + ban_time
                b.last_bans_times = f"{ban_times}"
                b.last_bans_causes = f"{ban_causes}"
                b.last_bans_names = f"{ban_names}"
                b.last_bans_dates = f"{ban_dates}"
                b.save()

                await kickUser(uid, chat_id)
                await deleteMessages(event.object.message.conversation_message_id, chat_id)
                await sendMessage(chat_id + 2000000000,
                                  messages.antispam_punishment(uid, name, nick, setting.setting, punishment[0],
                                                               setting.value, punishment[1]))
            return
    await add_msg_counter(chat_id, uid, audio)
