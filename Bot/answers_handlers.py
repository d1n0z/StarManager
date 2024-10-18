import datetime
import time
import traceback
from ast import literal_eval

import requests
import validators
from vkbottle_types.events.bot_events import MessageNew
from vkbottle_types.objects import MessagesMessageAttachmentType

import keyboard
import messages
from Bot.utils import getUserName, getChatName, sendMessage, editMessage, uploadImage, deleteMessages, punish, \
    getUserNickname
from config.config import REPORT_TO, SETTINGS_COUNTABLE_MULTIPLE_ARGUMENTS, PATH, SETTINGS_COUNTABLE_SPECIAL_LIMITS
from db import ReportAnswers, Notifs, TypeQueue, Settings, AntispamURLExceptions, Welcome, Captcha, WelcomeHistory, \
    Prefixes


async def report_handler(event: MessageNew):
    uid = event.object.message.from_id
    repansi = ReportAnswers.get_or_none(ReportAnswers.answering_id == uid)
    if repansi is None:
        return False
    answering_name = await getUserName(repansi.answering_id)
    name = await getUserName(repansi.uid)
    await deleteMessages([repansi.cmid, event.object.message.conversation_message_id], REPORT_TO)
    await sendMessage(repansi.chat_id + 2000000000, messages.report_answer(
        repansi.answering_id, answering_name, repansi.repid, event.object.message.text, repansi.uid, name))
    await sendMessage(REPORT_TO + 2000000000, messages.report_answered(
        repansi.answering_id, answering_name, repansi.repid, event.object.message.text, repansi.report_text, 
        repansi.uid, name, repansi.chat_id, await getChatName(repansi.chat_id)))
    repansi.delete_instance()
    return


async def queue_handler(event: MessageNew):
    uid = event.object.message.from_id
    chat_id = event.object.message.peer_id - 2000000000
    queue: TypeQueue = TypeQueue.get_or_none(TypeQueue.uid == uid, TypeQueue.chat_id == chat_id)
    if queue is None:
        return False
    additional = literal_eval(queue.additional)
    if queue.type not in ('captcha',):
        queue.delete_instance()

    if queue.type.startswith('notification_'):
        if queue.type == 'notification_text':
            name = additional['name']
            cmid = int(additional['cmid'])

            notif = Notifs.get(Notifs.name == name, Notifs.chat_id == chat_id)
            notif.text = event.object.message.text
            notif.save()

            msg = messages.notification_changed_text(name)
            await editMessage(msg, event.object.message.peer_id, cmid)

            notif = notif.select().where(notif.chat_id == chat_id, notif.name == name)[0]

            msg = messages.notification(notif.name, notif.text, notif.time, notif.every, notif.tag,
                                        notif.status)
            kb = keyboard.notification(uid, notif.status, notif.name)
            await sendMessage(chat_id + 2000000000, msg, kb)
            return
        elif queue.type == 'notification_time_change':
            ctime = event.object.message.text
            name = additional['name']
            cmid = int(additional['cmid'])
            ctype = additional['type']

            if ctype == 'single':
                try:
                    if (int(ctime.split(':')[0]) > 23 or int(ctime.split(':')[0]) < 0) or (
                            int(ctime.split(':')[1]) > 59 or int(ctime.split(':')[1]) < 0):
                        msg = messages.notification_changing_time_error()
                        await sendMessage(chat_id + 2000000000, msg)
                        return
                except:
                    msg = messages.notification_changing_time_error()
                    await sendMessage(chat_id + 2000000000, msg)
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
                        await sendMessage(chat_id + 2000000000, msg)
                        return
                except:
                    msg = messages.notification_changing_time_error()
                    await sendMessage(chat_id + 2000000000, msg)
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
                        await sendMessage(chat_id + 2000000000, msg)
                        return
                except:
                    msg = messages.notification_changing_time_error()
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                nctime = datetime.datetime.now() + datetime.timedelta(minutes=int(ctime))
                every = ctime

            notif = Notifs.get(Notifs.name == name, Notifs.chat_id == chat_id)
            notif.time = nctime.timestamp()
            notif.every = every
            notif.save()

            msg = messages.notification_changed_time(name)
            await editMessage(msg, event.object.message.peer_id, cmid)

            notif = notif.select().where(notif.chat_id == chat_id, notif.name == name)[0]

            msg = messages.notification(notif.name, notif.text, notif.time, notif.every, notif.tag,
                                        notif.status)
            kb = keyboard.notification(uid, notif.status, notif.name)
            await sendMessage(chat_id + 2000000000, msg, kb)
    elif queue.type.startswith('settings_'):
        if queue.type == 'settings_change_countable':
            setting = additional['setting']
            category = additional['category']
            cmid = additional['cmid']
            text = event.object.message.text
            kb = keyboard.settings_change_countable(uid, category, setting, onlybackbutton=True)
            if setting not in SETTINGS_COUNTABLE_MULTIPLE_ARGUMENTS:
                if setting not in SETTINGS_COUNTABLE_SPECIAL_LIMITS:
                    limit = range(0, 10001)
                else:
                    limit = SETTINGS_COUNTABLE_SPECIAL_LIMITS[setting]
                if not text.isdigit() or int(text) not in limit:
                    await editMessage(messages.settings_change_countable_digit_error(),
                                      event.object.message.peer_id, cmid, kb)
                    return
                chatsettings = Settings.get(Settings.chat_id == chat_id, Settings.setting == setting)
                chatsettings.value = int(text)
                chatsettings.save()
            else:
                if setting == 'nightmode':
                    try:
                        text = text.replace(' ', '')
                        args = text.split('-')
                        start = datetime.datetime.strptime(args[0], '%H:%M').replace(year=2024)
                        end = datetime.datetime.strptime(args[1], '%H:%M').replace(year=2024)
                        if end.hour <= start.hour:
                            end = end.replace(day=2)
                        if start.timestamp() >= end.timestamp():
                            raise
                    except:
                        traceback.print_exc()
                        await editMessage(messages.settings_change_countable_format_error(),
                                          event.object.message.peer_id, cmid, kb)
                        return
                    chatsettings = Settings.get(Settings.chat_id == chat_id, Settings.setting == setting)
                    val = f'0{start.hour}:' if start.hour < 10 else f'{start.hour}:'
                    val += f'0{start.minute}-' if start.minute < 10 else f'{start.minute}-'
                    val += f'0{end.hour}:' if end.hour < 10 else f'{end.hour}:'
                    val += f'0{end.minute}' if end.minute < 10 else f'{end.minute}'
                    chatsettings.value2 = val
                    chatsettings.save()
            await editMessage(messages.settings_change_countable_done(setting, text),
                              event.object.message.peer_id, cmid, kb)
        elif queue.type == 'settings_set_punishment':
            setting = additional['setting']
            category = additional['category']
            action = additional['action']
            cmid = additional['cmid']
            text = event.object.message.text
            kb = keyboard.settings_change_countable(uid, category, setting, onlybackbutton=True)
            if not text.isdigit() or int(text) <= 0 or int(text) >= 10000:
                await editMessage(messages.settings_change_countable_digit_error(), event.object.message.peer_id, cmid,
                                  kb)
                return
            chatsettings = Settings.get(Settings.chat_id == chat_id, Settings.setting == setting)
            chatsettings.punishment = f'{action}|{text}'
            chatsettings.save()
            await editMessage(messages.settings_set_punishment_countable(action, int(text)),
                              event.object.message.peer_id, cmid, kb)
        elif queue.type == 'settings_listaction':
            setting = additional['setting']
            action = additional['action']
            # type = additional['type']
            if setting == 'disallowLinks':
                if action == 'add':
                    url = event.object.message.text.replace(' ', '').replace('https://', '').replace('/', '')
                    if not (validators.url(url) or validators.domain(url)):
                        msg = messages.settings_change_countable_format_error()
                        await sendMessage(chat_id + 2000000000, msg)
                        return
                    AntispamURLExceptions.get_or_create(chat_id=chat_id, url=url)
                elif action == 'remove':
                    url = event.object.message.text.replace(' ', '').replace('https://', '').replace('/', '')
                    e = AntispamURLExceptions.get_or_none(chat_id=chat_id, url=url)
                    if e is None:
                        msg = messages.settings_change_countable_format_error()
                        await sendMessage(chat_id + 2000000000, msg)
                        return
                    e.delete_instance()
                else:
                    raise
                msg = messages.settings_listaction_done(setting, action, url)
                kb = keyboard.settings_change_countable(uid, 'antispam', onlybackbutton=True)
                await sendMessage(chat_id + 2000000000, msg, kb)
        elif queue.type.startswith('settings_set_welcome_'):
            welcome: Welcome = Welcome.get_or_create(chat_id=chat_id)[0]
            if queue.type == 'settings_set_welcome_text':
                if not event.object.message.text:
                    msg = messages.get(queue.type + '_no_text')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                welcome.msg = event.object.message.text
            elif queue.type == 'settings_set_welcome_photo':
                if (len(event.object.message.attachments) == 0 or
                        event.object.message.attachments[0].type != MessagesMessageAttachmentType.PHOTO):
                    msg = messages.get(queue.type + '_not_photo')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                r = requests.get(event.object.message.attachments[0].photo.sizes[-1].url)
                with open(f'{PATH}media/temp/{uid}welcome.jpg', "wb") as f:
                    f.write(r.content)
                    f.close()
                r.close()
                welcome.photo = await uploadImage(f'{PATH}media/temp/{uid}welcome.jpg')
            elif queue.type == 'settings_set_welcome_url':
                if not welcome.msg and not welcome.url:
                    msg = messages.get(queue.type + '_empty_text_url')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                if len(' '.join(welcome.msg.split()[1:])) > 40:
                    msg = messages.get(queue.type + '_limit_text')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                if len(' '.join(welcome.msg.split()[1:])) == 0 or welcome.msg.count('\n') > 0:
                    msg = messages.settings_change_countable_format_error()
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                text = event.object.message.text.split()
                if len(text) < 2:
                    msg = messages.settings_change_countable_format_error()
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                if not validators.url(text[-1]):
                    msg = messages.get(queue.type + '_no_url')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                welcome.url = text[-1]
                welcome.button_label = ' '.join(text[0:-1])
            welcome.save()
            msg = messages.get(f'{queue.type}_done')
            kb = keyboard.settings_change_countable(uid, "main", "welcome", onlybackbutton=True)
            await sendMessage(chat_id + 2000000000, msg, kb)
    elif queue.type == 'captcha':
        c: Captcha = Captcha.select().where(
            Captcha.chat_id == chat_id, Captcha.uid == uid).order_by(Captcha.exptime.desc())[0]
        if c is None or c.result is None:
            return
        if c.result.strip() != event.object.message.text.strip():
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            return

        name = await getUserName(uid)
        await sendMessage(chat_id + 2000000000, messages.captcha_pass(
            uid, name, datetime.datetime.now().strftime('%H:%M:%S %Y.%m.%d')))
        TypeQueue.delete().where(TypeQueue.uid == uid, TypeQueue.chat_id == chat_id).execute()

        if s := Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == 'welcome'):
            welcome = Welcome.get_or_none(Welcome.chat_id == chat_id)
            if welcome is not None and s.pos:
                await sendMessage(event.object.message.peer_id, welcome.msg.replace('%name%', f"[id{uid}|{name}]"),
                                  keyboard.welcome(welcome.url, welcome.button_label), welcome.photo)
        await deleteMessages([i.cmid for i in Captcha.select().where(Captcha.chat_id == chat_id, Captcha.uid == uid)],
                             chat_id)
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
        Captcha.delete().where(Captcha.chat_id == chat_id, Captcha.uid == uid).execute()
    elif queue.type.startswith('prefix'):
        if queue.type == 'prefix_add':
            await deleteMessages(additional['cmid'], chat_id)
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            if len(event.object.message.text) > 2:
                await sendMessage(event.object.message.peer_id, messages.addprefix_too_long(),
                                  keyboard.prefix_back(uid))
                return
            Prefixes.get_or_create(uid=uid, prefix=event.object.message.text)
            await sendMessage(event.object.message.peer_id,
                              messages.addprefix(uid, await getUserName(uid), await getUserNickname(uid, chat_id),
                                                 event.object.message.text), keyboard.prefix_back(uid))
        elif queue.type == 'prefix_del':
            await deleteMessages(additional['cmid'], chat_id)
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            if not (p := Prefixes.get_or_none(Prefixes.uid == uid, Prefixes.prefix == event.object.message.text)):
                await sendMessage(event.object.message.peer_id, messages.delprefix_not_found(event.object.message.text),
                                  keyboard.prefix_back(uid))
                return
            p.delete_instance()
            await sendMessage(event.object.message.peer_id,
                              messages.delprefix(uid, await getUserName(uid), await getUserNickname(uid, chat_id),
                                                 event.object.message.text), keyboard.prefix_back(uid))
    return


async def answer_handler(event: MessageNew):
    chat_id = event.object.message.peer_id - 2000000000
    if chat_id == REPORT_TO:
        return await report_handler(event)
    return await queue_handler(event)
