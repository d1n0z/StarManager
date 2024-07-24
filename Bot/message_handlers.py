import datetime
import time
from ast import literal_eval

from vkbottle_types.events import MessageNew
from vkbottle_types.objects import MessagesMessageAttachmentType

import keyboard
import messages
from Bot.action_handlers import action_handle
from Bot.add_msg_count import add_msg_counter
from Bot.checkers import getUChatLimit, getSilence
from Bot.utils import getUserName, getUserLastMessage, getUserAccessLevel, getUserMute, getChatName, addDailyTask
from config.config import API, REPORT_TO, ADMINS, DEVS
from db import Settings, AllUsers, AllChats, ReportAnswers, TypeQueue, Notifs, Filters, MessagesHistory


async def message_handle(event: MessageNew) -> None:
    if action := event.object.message.action:
        uid = event.object.message.from_id
        chat_id = event.object.message.peer_id - 2000000000
        setKick = Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == 'setKick')
        if setKick is not None:
            setKick = setKick.pos
        else:
            setKick = 1

        await action_handle(action, setKick, chat_id, uid)
        return
    uid = event.object.message.from_id
    msg = event.object.message.text
    msgtime = event.object.message.date
    msgwithcaps = event.object.message.text
    chat_id = event.object.message.peer_id - 2000000000
    AllUsers.get_or_create(uid=uid)
    AllChats.get_or_create(chat_id=chat_id)
    # MessagesHistory.create(id=event.object.message.id, cmid=event.object.message.conversation_message_id,
    #                        chat_id=chat_id, from_id=uid, text=msg, time=time.time())
    if chat_id < 0:
        chat_id += 2000000000
        if len(event.object.message.attachments) == 0:
            msg = messages.pm()
            await API.messages.send(random_id=0, user_id=chat_id, message=msg)
            return
        elif event.object.message.attachments[0].market is not None:
            msg = messages.pm_market()
            await API.messages.send(random_id=0, user_id=chat_id, message=msg, keyboard=keyboard.pm_market())
            return

    if int(chat_id) == REPORT_TO:
        try:
            repansi = ReportAnswers.get(ReportAnswers.answering_id == uid)
            answering_id = repansi.answering_id
            uid = repansi.uid
            chat_id = repansi.chat_id
            repid = repansi.repid
            reptext = repansi.report_text

            answering_name = await getUserName(answering_id)
            name = await getUserName(uid)

            chat_name = await getChatName(chat_id)

            # try:
            #     cmids = await API.messages.get_important_messages()
            #     cmids = [i.conversation_message_id for i in cmids.messages.items]
            #     await deleteMessages(cmids, chat_id)
            # except:
            #     traceback.print_exc()

            msged = messages.report_answered(answering_id, answering_name, repid, msg, reptext, uid, name, chat_id,
                                             chat_name)
            msg = messages.report_answer(answering_id, answering_name, repid, msg, uid, name)
            try:
                await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                await API.messages.send(random_id=0, chat_id=REPORT_TO, message=msged)
            except:
                await API.messages.send(random_id=0, chat_id=REPORT_TO, message='❌ Не удалось отправить ответ')
            repansi.delete_instance()
            return
        except:
            pass

    try:
        queue = TypeQueue.get(TypeQueue.uid == uid, TypeQueue.chat_id == chat_id)
        qtype = queue.type
        additional = literal_eval(queue.additional)
        queue.delete_instance()
        if qtype == 'notification_text':
            text = msgwithcaps
            name = additional['name']
            cmid = int(additional['cmid'])

            notif = Notifs.get(Notifs.name == name, Notifs.chat_id == chat_id)
            notif.text = text
            notif.save()

            msg = messages.notification_changed_text(name)
            await API.messages.edit(peer_id=chat_id + 2000000000, message=msg, conversation_message_id=cmid)

            notif = notif.select().where(notif.chat_id == chat_id, notif.name == name)[0]

            msg = messages.notification(notif.name, notif.text, notif.time, notif.every, notif.tag,
                                        notif.status)
            kb = keyboard.notification(uid, notif.status, notif.name)
            await API.messages.send(random_id=0, chat_id=chat_id, message=msg, keyboard=kb)
            return
        elif qtype == 'notification_time_change':
            ctime = msgwithcaps
            name = additional['name']
            cmid = int(additional['cmid'])
            ctype = additional['type']

            if ctype == 'single':
                try:
                    if (int(ctime.split(':')[0]) > 23 or int(ctime.split(':')[0]) < 0) or (
                            int(ctime.split(':')[1]) > 59 or int(ctime.split(':')[1]) < 0):
                        msg = messages.notification_changing_time_error()
                        await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                        return
                except:
                    msg = messages.notification_changing_time_error()
                    await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                    return
                ctime = datetime.datetime.strptime(ctime, '%H:%M')
                nctime = datetime.datetime.now().replace(hour=ctime.hour, minute=ctime.minute)
                if nctime.timestamp() < time.time():
                    nctime += datetime.timedelta(days=1)
                every = 0
            elif ctype == 'everyday':
                try:
                    if (int(ctime.split(':')[0]) > 23 or int(ctime.split(':')[0]) < 0) or (
                            int(ctime.split(':')[1]) > 59 or int(ctime.split(':')[1]) < 0):
                        msg = messages.notification_changing_time_error()
                        await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                        return
                except:
                    msg = messages.notification_changing_time_error()
                    await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                    return
                ctime = datetime.datetime.strptime(ctime, '%H:%M')
                nctime = datetime.datetime.now().replace(hour=ctime.hour, minute=ctime.minute)
                if nctime.timestamp() < time.time():
                    nctime += datetime.timedelta(days=1)
                every = 1440
            else:
                try:
                    if int(ctime.split()[0]) < 0:
                        msg = messages.notification_changing_time_error()
                        await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                        return
                except:
                    msg = messages.notification_changing_time_error()
                    await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                    return
                nctime = datetime.datetime.now() + datetime.timedelta(minutes=int(ctime))
                every = ctime

            notif = Notifs.get(Notifs.name == name, Notifs.chat_id == chat_id)
            notif.time = nctime.timestamp()
            notif.every = every
            notif.save()

            msg = messages.notification_changed_time(name)
            await API.messages.edit(peer_id=chat_id + 2000000000, message=msg, conversation_message_id=cmid)

            notif = notif.select().where(notif.chat_id == chat_id, notif.name == name)[0]

            msg = messages.notification(notif.name, notif.text, notif.time, notif.every, notif.tag,
                                        notif.status)
            kb = keyboard.notification(uid, notif.status, notif.name)
            await API.messages.send(random_id=0, chat_id=chat_id, message=msg, keyboard=kb)
        return
    except:
        pass

    if uid in ADMINS:
        print(f'{uid}({chat_id}): {msg}')

    if Filters.get_or_none(Filters.chat_id == chat_id,
                           Filters.filter << [i.lower() for i in msg.lower().split()]) is not None:
        await API.messages.delete(cmids=event.object.message.conversation_message_id, peer_id=chat_id + 2000000000,
                                  delete_for_all=1)
        return

    uacc = await getUserAccessLevel(uid, chat_id)
    chlim = await getUChatLimit(msgtime, await getUserLastMessage(uid, chat_id, 0), uacc, chat_id)
    timeout = await getSilence(chat_id)
    if (chlim and uacc <= 0) or await getUserMute(uid, chat_id) > int(msgtime) or (timeout and uacc == 0):
        try:
            await API.messages.delete(cmids=event.object.message.conversation_message_id,
                                      peer_id=chat_id + 2000000000, delete_for_all=True)
            return
        except:
            pass

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

    if uid in DEVS and '/getxp' in msg:
        addxp = int(msg.split()[1])
    else:
        addxp = 0

    await add_msg_counter(chat_id, uid, audio, addxp)
