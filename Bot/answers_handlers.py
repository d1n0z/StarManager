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
from Bot.utils import getUserName, getChatName, sendMessage, editMessage, uploadImage, deleteMessages, getUserNickname
from config.config import REPORT_TO, SETTINGS_COUNTABLE_MULTIPLE_ARGUMENTS, PATH, SETTINGS_COUNTABLE_SPECIAL_LIMITS
from db import pool


async def report_handler(event: MessageNew):
    uid = event.object.message.from_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            repansi = await (await c.execute(
                'select id, answering_id, uid, chat_id, repid, report_text, cmid from reportanswers '
                'where answering_id=%s', (uid,))).fetchone()
            if repansi is None:
                return False
            await c.execute('delete from reportanswers where id=%s', (repansi[0],))
            await conn.commit()
    answering_name = await getUserName(repansi[1])
    name = await getUserName(repansi[2])
    await deleteMessages([repansi[6], event.object.message.conversation_message_id], REPORT_TO)
    await sendMessage(repansi[3] + 2000000000, messages.report_answer(
        repansi[1], answering_name, repansi[4], event.object.message.text, repansi[2], name))
    await sendMessage(REPORT_TO + 2000000000, messages.report_answered(
        repansi[1], answering_name, repansi[4], event.object.message.text, repansi[5], 
        repansi[2], name, repansi[3], await getChatName(repansi[3])))
    return


async def queue_handler(event: MessageNew):
    uid = event.object.message.from_id
    chat_id = event.object.message.peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            queue = await (await c.execute(
                'select id, chat_id, uid, "type", additional from typequeue where chat_id=%s and uid=%s',
                (chat_id, uid))).fetchone()
            if not queue:
                return False
            if queue[3] not in ('captcha',):
                await c.execute('delete from typequeue where id=%s', (queue[0],))
                await conn.commit()
    additional = literal_eval(queue[4])

    if queue[3].startswith('notification_'):
        if queue[3] == 'notification_text':
            name = additional['name']
            cmid = int(additional['cmid'])

            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    notif = await (await c.execute(
                        'update notifications set text = %s where name=%s and chat_id=%s returning name, time, every, '
                        'tag, status', (event.object.message.text, name, chat_id))).fetchone()
                    await conn.commit()

            msg = messages.notification_changed_text(name)
            await editMessage(msg, event.object.message.peer_id, cmid)

            msg = messages.notification(notif[0], event.object.message.text, notif[1], notif[2], notif[3],
                                        notif[4])
            kb = keyboard.notification(uid, notif[4], notif[0])
            await sendMessage(chat_id + 2000000000, msg, kb)
            return
        elif queue[3] == 'notification_time_change':
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

            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    notif = await (await c.execute(
                        'update notifications set time = %s, every = %s where name=%s and chat_id=%s '
                        'returning name, text, time, every, tag, status',
                        (nctime.timestamp(), every, name, chat_id))).fetchone()
                    await conn.commit()

            msg = messages.notification_changed_time(name)
            await editMessage(msg, event.object.message.peer_id, cmid)

            msg = messages.notification(notif[0], notif[1], notif[2], notif[3], notif[4], notif[5])
            kb = keyboard.notification(uid, notif[5], notif[0])
            await sendMessage(chat_id + 2000000000, msg, kb)
    elif queue[3].startswith('settings_'):
        if queue[3] == 'settings_change_countable':
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
                async with (await pool()).connection() as conn:
                    async with conn.cursor() as c:
                        await c.execute('update settings set value = %s where chat_id=%s and setting=%s',
                                        (int(text), chat_id, setting))
                        await conn.commit()
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
                    val = f'0{start.hour}:' if start.hour < 10 else f'{start.hour}:'
                    val += f'0{start.minute}-' if start.minute < 10 else f'{start.minute}-'
                    val += f'0{end.hour}:' if end.hour < 10 else f'{end.hour}:'
                    val += f'0{end.minute}' if end.minute < 10 else f'{end.minute}'
                    async with (await pool()).connection() as conn:
                        async with conn.cursor() as c:
                            await c.execute('update settings set value2 = %s where chat_id=%s and setting=%s',
                                            (val, chat_id, setting))
                            await conn.commit()
            await editMessage(messages.settings_change_countable_done(setting, text),
                              event.object.message.peer_id, cmid, kb)
        elif queue[3] == 'settings_set_punishment':
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
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    await c.execute('update settings set punishment = %s where chat_id=%s and setting=%s',
                                    (f'{action}|{text}', chat_id, setting))
                    await conn.commit()
            await editMessage(messages.settings_set_punishment_countable(action, int(text)),
                              event.object.message.peer_id, cmid, kb)
        elif queue[3] == 'settings_listaction':
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
                    async with (await pool()).connection() as conn:
                        async with conn.cursor() as c:
                            if not await (await c.execute(
                                    'select id from antispammurlexceptions where chat_id=%s and url=%s',
                                    (chat_id, url))).fetchone():
                                await c.execute('insert into antispammurlexceptions (chat_id, url) values (%s, %s)',
                                                (chat_id, url))
                            await conn.commit()
                elif action == 'remove':
                    url = event.object.message.text.replace(' ', '').replace('https://', '').replace('/', '')
                    async with (await pool()).connection() as conn:
                        async with conn.cursor() as c:
                            if not await (await c.execute(
                                    'delete from antispammurlexceptions where chat_id=%s and url=%s',
                                    (chat_id, url))).fetchone():
                                msg = messages.settings_change_countable_format_error()
                                await sendMessage(chat_id + 2000000000, msg)
                                return
                            await conn.commit()
                else:
                    raise
                msg = messages.settings_listaction_done(setting, action, url)
                kb = keyboard.settings_change_countable(uid, 'antispam', onlybackbutton=True)
                await sendMessage(chat_id + 2000000000, msg, kb)
        elif queue[3].startswith('settings_set_welcome_'):
            if queue[3] == 'settings_set_welcome_text':
                if not event.object.message.text:
                    msg = messages.get(queue[3] + '_no_text')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                async with (await pool()).connection() as conn:
                    async with conn.cursor() as c:
                        await c.execute(
                            'update welcome set msg = %s where chat_id=%s', (event.object.message.text, chat_id))
                        await conn.commit()
            elif queue[3] == 'settings_set_welcome_photo':
                if (len(event.object.message.attachments) == 0 or
                        event.object.message.attachments[0].type != MessagesMessageAttachmentType.PHOTO):
                    msg = messages.get(queue[3] + '_not_photo')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                r = requests.get(event.object.message.attachments[0].photo.sizes[-1].url)
                with open(f'{PATH}media/temp/{uid}welcome.jpg', "wb") as f:
                    f.write(r.content)
                    f.close()
                r.close()
                async with (await pool()).connection() as conn:
                    async with conn.cursor() as c:
                        await c.execute('update welcome set photo = %s where chat_id=%s',
                                        (await uploadImage(f'{PATH}media/temp/{uid}welcome.jpg'), chat_id))
                        await conn.commit()
            elif queue[3] == 'settings_set_welcome_url':
                async with (await pool()).connection() as conn:
                    async with conn.cursor() as c:
                        welcome = await (await c.execute(
                            'select msg, url from welcome where chat_id=%s', (chat_id,))).fetchone()
                if welcome and not welcome[0] and not welcome[1]:
                    msg = messages.get(queue[3] + '_empty_text_url')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                if len(' '.join(event.object.message.text.split()[1:])) > 40:
                    msg = messages.get(queue[3] + '_limit_text')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                if (len(' '.join(event.object.message.text.split()[1:])) == 0 or
                        event.object.message.text.count('\n') > 0):
                    msg = messages.settings_change_countable_format_error()
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                text = event.object.message.text.split()
                if len(text) < 2:
                    msg = messages.settings_change_countable_format_error()
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                if not validators.url(text[-1]):
                    msg = messages.get(queue[3] + '_no_url')
                    await sendMessage(chat_id + 2000000000, msg)
                    return
                async with (await pool()).connection() as conn:
                    async with conn.cursor() as c:
                        await c.execute('update welcome set url = %s, button_label = %s where chat_id=%s',
                                        (text[-1], ' '.join(text[0:-1]), chat_id))
                        await conn.commit()
            msg = messages.get(f'{queue[3]}_done')
            kb = keyboard.settings_change_countable(uid, "main", "welcome", onlybackbutton=True)
            await sendMessage(chat_id + 2000000000, msg, kb)
    elif queue[3] == 'captcha':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                c = await (await c.execute('select result from captcha where chat_id=%s and uid=%s order by exptime '
                                           'desc', (chat_id, uid))).fetchone()
        if c is None or c[0] is None:
            return
        if c[0].strip() != event.object.message.text.strip():
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            return

        name = await getUserName(uid)
        await sendMessage(chat_id + 2000000000, messages.captcha_pass(
            uid, name, datetime.datetime.now().strftime('%H:%M:%S %Y.%m.%d')))
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('delete from typequeue where chat_id=%s and uid=%s', (chat_id, uid))
                s = await (await c.execute(
                    'select pos from settings where chat_id=%s and setting=\'welcome\'', (chat_id,))).fetchone()
                welcome = await (await c.execute('select msg, url, button_label, photo from welcome where chat_id=%s',
                                                 (chat_id,))).fetchone()
                cmsgs = await (await c.execute('select cmid from captcha where chat_id=%s and uid=%s',
                                               (chat_id, uid))).fetchall()
                await c.execute('delete from captcha where chat_id=%s and uid=%s', (chat_id, uid))
                await conn.commit()
        if s and s[0] and welcome:
            await sendMessage(event.object.message.peer_id, welcome[0].replace('%name%', f"[id{uid}|{name}]"),
                              keyboard.welcome(welcome[1], welcome[2]), welcome[3])
        await deleteMessages([i[0] for i in cmsgs], chat_id)
        await deleteMessages(event.object.message.conversation_message_id, chat_id)
    elif queue[3].startswith('prefix'):
        if queue[3] == 'prefix_add':
            await deleteMessages(additional['cmid'], chat_id)
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            if len(event.object.message.text) > 2:
                await sendMessage(event.object.message.peer_id, messages.addprefix_too_long(),
                                  keyboard.prefix_back(uid))
                return
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    if not await (await c.execute('select id from prefix where uid=%s and prefix=%s',
                                                  (uid, event.object.message.text))).fetchone():
                        await c.execute(
                            'insert into prefix (uid, prefix) values (%s, %s)', (uid, event.object.message.text))
                        await conn.commit()
            await sendMessage(event.object.message.peer_id,
                              messages.addprefix(uid, await getUserName(uid), await getUserNickname(uid, chat_id),
                                                 event.object.message.text), keyboard.prefix_back(uid))
        elif queue[3] == 'prefix_del':
            await deleteMessages(additional['cmid'], chat_id)
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    if not (await c.execute('delete from prefix where uid=%s and prefix=%s',
                                            (uid, event.object.message.text))).rowcount:
                        await sendMessage(
                            event.object.message.peer_id, messages.delprefix_not_found(event.object.message.text),
                            keyboard.prefix_back(uid))
                        return
                    await conn.commit()
            await sendMessage(event.object.message.peer_id,
                              messages.delprefix(uid, await getUserName(uid), await getUserNickname(uid, chat_id),
                                                 event.object.message.text), keyboard.prefix_back(uid))
    return


async def answer_handler(event: MessageNew):
    chat_id = event.object.message.peer_id - 2000000000
    if chat_id == REPORT_TO:
        return await report_handler(event)
    return await queue_handler(event)
