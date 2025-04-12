import datetime
import re
import time
import traceback
from ast import literal_eval

import requests
from vkbottle_types.events.bot_events import MessageNew
from vkbottle_types.objects import MessagesMessageAttachmentType

import keyboard
import messages
from Bot.utils import (getUserName, getChatName, sendMessage, editMessage, uploadImage, deleteMessages,
                       getUserNickname, hex_to_rgb, whoiscachedurl)
from config.config import REPORT_TO, SETTINGS_COUNTABLE_MULTIPLE_ARGUMENTS, PATH, SETTINGS_COUNTABLE_SPECIAL_LIMITS
from db import pool


async def report_handler(event: MessageNew):
    async with (await pool()).acquire() as conn:
        if not (repansi := await conn.fetchrow(
                'select id, answering_id, uid, chat_id, repid, report_text, cmid, photos from reportanswers '
                'where answering_id=$1', event.object.message.from_id)):
            return False
        await conn.execute('delete from reportanswers where id=$1', repansi[0])
    answering_name = await getUserName(repansi[1])
    name = await getUserName(repansi[2])
    await deleteMessages([repansi[6], event.object.message.conversation_message_id], REPORT_TO)
    await sendMessage(repansi[3] + 2000000000, messages.report_answer(
        repansi[1], answering_name, repansi[4], event.object.message.text, repansi[2], name, repansi[5]))
    await sendMessage(REPORT_TO + 2000000000, messages.report_answered(
        repansi[1], answering_name, repansi[4], event.object.message.text, repansi[5],
        repansi[2], name, repansi[3], await getChatName(repansi[3])))
    return


async def queue_handler(event: MessageNew):
    uid = event.object.message.from_id
    chat_id = event.object.message.peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        queue = await conn.fetchrow(
            'select id, chat_id, uid, "type", additional from typequeue where chat_id=$1 and uid=$2',
            chat_id, uid)
        if not queue:
            return False
        if queue[3] not in ('captcha',):
            await conn.execute('delete from typequeue where id=$1', queue[0])
    additional = literal_eval(queue[4])

    if queue[3].startswith('notification_'):
        if queue[3] == 'notification_text':
            name = additional['name']
            cmid = int(additional['cmid'])

            async with (await pool()).acquire() as conn:
                notif = await conn.fetchrow(
                    'update notifications set text = $1 where name=$2 and chat_id=$3 returning name, time, every, '
                    'tag, status', event.object.message.text, name, chat_id)

            await editMessage(messages.notification_changed_text(name), event.object.message.peer_id, cmid)
            return await sendMessage(chat_id + 2000000000, messages.notification(
                notif[0], event.object.message.text, notif[1], notif[2], notif[3], notif[4]),
                                     keyboard.notification(uid, notif[4], notif[0]))
        elif queue[3] == 'notification_time_change':
            ctime = event.object.message.text
            ctype = additional['type']

            if ctype == 'single':
                try:
                    if (int(ctime.split(':')[0]) > 23 or int(ctime.split(':')[0]) < 0) or (
                            int(ctime.split(':')[1]) > 59 or int(ctime.split(':')[1]) < 0):
                        return await sendMessage(chat_id + 2000000000, messages.notification_changing_time_error())
                except:
                    return await sendMessage(chat_id + 2000000000, messages.notification_changing_time_error())
                ctime = datetime.datetime.strptime(ctime, '%H:%M')
                nctime = datetime.datetime.now().replace(hour=ctime.hour, minute=ctime.minute)
                if nctime.timestamp() < time.time():
                    nctime += datetime.timedelta(days=1)
                every = 0
            elif ctype == 'everyday':
                try:
                    if (int(ctime.split(':')[0]) > 23 or int(ctime.split(':')[0]) < 0) or (
                            int(ctime.split(':')[1]) > 59 or int(ctime.split(':')[1]) < 0):
                        return await sendMessage(chat_id + 2000000000, messages.notification_changing_time_error())
                except:
                    return await sendMessage(chat_id + 2000000000, messages.notification_changing_time_error())
                ctime = datetime.datetime.strptime(ctime, '%H:%M')
                nctime = datetime.datetime.now().replace(hour=ctime.hour, minute=ctime.minute)
                if nctime.timestamp() < time.time():
                    nctime += datetime.timedelta(days=1)
                every = 1440
            else:
                try:
                    if int(ctime.split()[0]) < 0:
                        return await sendMessage(chat_id + 2000000000, messages.notification_changing_time_error())
                except:
                    return await sendMessage(chat_id + 2000000000, messages.notification_changing_time_error())
                nctime = datetime.datetime.now() + datetime.timedelta(minutes=int(ctime))
                every = ctime

            name = additional['name']
            async with (await pool()).acquire() as conn:
                notif = await conn.fetchrow(
                    'update notifications set time = $1, every = $2 where name=$3 and chat_id=$4 '
                    'returning name, text, time, every, tag, status', nctime.timestamp(), int(every), name, chat_id)

            cmid = int(additional['cmid'])
            await editMessage(messages.notification_changed_time(name), event.object.message.peer_id, cmid)
            await sendMessage(chat_id + 2000000000, messages.notification(*notif), keyboard.notification(
                uid, notif[5], notif[0]))
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
                async with (await pool()).acquire() as conn:
                    await conn.execute('update settings set value = $1 where chat_id=$2 and setting=$3',
                                       int(text), chat_id, setting)
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
                    async with (await pool()).acquire() as conn:
                        await conn.execute('update settings set value2 = $1 where chat_id=$2 and setting=$3',
                                           val, chat_id, setting)
            await editMessage(messages.settings_change_countable_done(setting, text),
                              event.object.message.peer_id, cmid, kb)
        elif queue[3] == 'settings_set_punishment':
            setting = additional['setting']
            cmid = additional['cmid']
            text = event.object.message.text
            category = additional['category']
            kb = keyboard.settings_change_countable(uid, category, setting, onlybackbutton=True)
            if not text.isdigit() or int(text) <= 0 or int(text) >= 10000:
                await editMessage(messages.settings_change_countable_digit_error(), event.object.message.peer_id, cmid,
                                  kb)
                return
            action = additional['action']
            async with (await pool()).acquire() as conn:
                await conn.execute('update settings set punishment = $1 where chat_id=$2 and setting=$3',
                                   f'{action}|{text}', chat_id, setting)
            await editMessage(messages.settings_set_punishment_countable(action, int(text)),
                              event.object.message.peer_id, cmid, kb)
        elif queue[3].startswith('settings_set_welcome_'):
            if queue[3] == 'settings_set_welcome_text':
                if not event.object.message.text:
                    return await sendMessage(chat_id + 2000000000, messages.get(queue[3] + '_no_text'))
                async with (await pool()).acquire() as conn:
                    if not await conn.fetchval('update welcome set msg = $1 where chat_id=$2 returning 1',
                                               event.object.message.text, chat_id):
                        await conn.execute('insert into welcome (chat_id, msg) values ($1, $2)',
                                           chat_id, event.object.message.text)
            elif queue[3] == 'settings_set_welcome_photo':
                if (len(event.object.message.attachments) == 0 or
                        event.object.message.attachments[0].type != MessagesMessageAttachmentType.PHOTO):
                    return await sendMessage(chat_id + 2000000000, messages.get(queue[3] + '_not_photo'))
                r = requests.get(event.object.message.attachments[0].photo.sizes[-1].url)
                with open(f'{PATH}media/temp/{uid}welcome.jpg', "wb") as f:
                    f.write(r.content)
                photo = await uploadImage(f'{PATH}media/temp/{uid}welcome.jpg')
                async with (await pool()).acquire() as conn:
                    if not await conn.fetchval('update welcome set photo = $1 where chat_id=$2 returning 1',
                                               photo, chat_id):
                        await conn.execute('insert into welcome (chat_id, photo) values ($1, $2)', chat_id, photo)
            elif queue[3] == 'settings_set_welcome_url':
                async with (await pool()).acquire() as conn:
                    welcome = await conn.fetchrow('select msg, url from welcome where chat_id=$1', chat_id)
                if welcome and not welcome[0] and not welcome[1]:
                    return await sendMessage(chat_id + 2000000000, messages.get(queue[3] + '_empty_text_url'))
                if len(' '.join(event.object.message.text.split()[1:])) > 40:
                    return await sendMessage(chat_id + 2000000000, messages.get(queue[3] + '_limit_text'))
                if (len(' '.join(event.object.message.text.split()[1:])) == 0 or
                        event.object.message.text.count('\n') > 0):
                    return await sendMessage(chat_id + 2000000000, messages.settings_change_countable_format_error())
                text = event.object.message.text.split()
                if len(text) < 2:
                    return await sendMessage(chat_id + 2000000000, messages.settings_change_countable_format_error())
                try:
                    if not whoiscachedurl(text[-1]):
                        raise Exception
                except:
                    return await sendMessage(chat_id + 2000000000, messages.get(queue[3] + '_no_url'))
                async with (await pool()).acquire() as conn:
                    if not await conn.fetchval('update welcome set url = $1, button_label = $2 where chat_id=$3 '
                                               'returning 1', text[-1], ' '.join(text[0:-1]), chat_id):
                        await conn.execute('insert into welcome (chat_id, url, button_label) values ($1, $2, $3)',
                                           chat_id, text[-1], ' '.join(text[0:-1]))
            await sendMessage(chat_id + 2000000000, messages.get(f'{queue[3]}_done'),
                              keyboard.settings_change_countable(uid, "main", "welcome", onlybackbutton=True))
        elif queue[3] == 'settings_listaction':
            setting = additional['setting']
            # type = additional['type']
            if setting == 'disallowLinks':
                action = additional['action']
                if action == 'add':
                    url = event.object.message.text.replace(' ', '')
                    try:
                        if not whoiscachedurl(url):
                            raise
                    except:
                        return await sendMessage(chat_id + 2000000000,
                                                 messages.settings_change_countable_format_error())
                    async with (await pool()).acquire() as conn:
                        if not await conn.fetchval('select exists(select 1 from antispamurlexceptions where '
                                                   'chat_id=$1 and url=$2)', chat_id, url):
                            await conn.execute('insert into antispamurlexceptions (chat_id, url) values ($1, $2)',
                                               chat_id, url)
                elif action == 'remove':
                    url = event.object.message.text.replace(' ', '').replace('https://', '').replace('/', '')
                    async with (await pool()).acquire() as conn:
                        if not await conn.fetchval(
                                'delete from antispammurlexceptions where chat_id=$1 and url=$2 returning 1',
                                chat_id, url):
                            return await sendMessage(
                                chat_id + 2000000000, messages.settings_change_countable_format_error())
                else:
                    raise
                await sendMessage(chat_id + 2000000000, messages.settings_listaction_done(setting, action, url),
                                  keyboard.settings_change_countable(uid, 'antispam', onlybackbutton=True))
    elif queue[3].startswith('premmenu_action_'):
        if queue[3] == 'premmenu_action_border_color':
            data = event.object.message.text
            rgb = data.replace(' ', '').split(',')
            if len(rgb) == 3 and all(255 >= int(i) >= 0 for i in rgb):
                color = ('(' + ','.join(rgb) + ')')
            elif re.search(r'^#[0-9a-fA-F]{6}$', data):
                color = f'({",".join(str(i) for i in hex_to_rgb(data))})'
            else:
                return await sendMessage(chat_id + 2000000000, messages.settings_change_countable_format_error())
            async with (await pool()).acquire() as conn:
                if not await conn.fetchval('update premmenu set value = $1 where uid=$2 and setting=$3 returning 1',
                                           color, uid, 'border_color'):
                    await conn.execute('insert into premmenu (uid, setting, value) values ($1, $2, $3)',
                                       uid, 'border_color', color)
            await sendMessage(chat_id + 2000000000, messages.premmenu_action_complete(
                'border_color', color.replace('(', '').replace(')', '')), keyboard.premmenu_back(uid))
    elif queue[3] == 'captcha':
        async with (await pool()).acquire() as conn:
            c = await conn.fetchval('select result from captcha where chat_id=$1 and uid=$2 order by exptime desc',
                                    chat_id, uid)
        if c is None:
            return
        if c.strip() != event.object.message.text.strip():
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            return

        name = await getUserName(uid)
        await sendMessage(chat_id + 2000000000, messages.captcha_pass(
            uid, name, datetime.datetime.now().strftime('%H:%M:%S %Y.%m.%d')))
        async with (await pool()).acquire() as conn:
            await conn.execute('delete from typequeue where chat_id=$1 and uid=$2', chat_id, uid)
            s = await conn.fetchrow('select pos from settings where chat_id=$1 and setting=\'welcome\'', chat_id)
            welcome = await conn.fetchrow(
                'select msg, url, button_label, photo from welcome where chat_id=$1', chat_id)
            cmsgs = await conn.fetch(
                'select cmid from captcha where chat_id=$1 and uid=$2', chat_id, uid)
            await conn.execute('delete from captcha where chat_id=$1 and uid=$2', chat_id, uid)
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
            async with (await pool()).acquire() as conn:
                if not await conn.fetchval('select exists(select 1 from prefix where uid=$1 and prefix=$2)',
                                           uid, event.object.message.text):
                    await conn.execute(
                        'insert into prefix (uid, prefix) values ($1, $2)', uid, event.object.message.text)
            await sendMessage(event.object.message.peer_id,
                              messages.addprefix(uid, await getUserName(uid), await getUserNickname(uid, chat_id),
                                                 event.object.message.text), keyboard.prefix_back(uid))
        elif queue[3] == 'prefix_del':
            await deleteMessages(additional['cmid'], chat_id)
            await deleteMessages(event.object.message.conversation_message_id, chat_id)
            async with (await pool()).acquire() as conn:
                if not await conn.fetchval('delete from prefix where uid=$1 and prefix=$2 returning 1',
                                           uid, event.object.message.text):
                    await sendMessage(
                        event.object.message.peer_id, messages.delprefix_not_found(event.object.message.text),
                        keyboard.prefix_back(uid))
                    return
            await sendMessage(event.object.message.peer_id,
                              messages.delprefix(uid, await getUserName(uid), await getUserNickname(uid, chat_id),
                                                 event.object.message.text), keyboard.prefix_back(uid))
    return


async def answer_handler(event: MessageNew):
    if event.object.message.peer_id - 2000000000 == REPORT_TO:
        return await report_handler(event)
    return await queue_handler(event)
