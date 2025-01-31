import asyncio
import calendar
import os
import subprocess
import time
import traceback
from datetime import datetime
from zipfile import ZipFile

import aiocron
import yadisk
from loguru import logger

import messages
from Bot.tgbot import tgbot
from Bot.utils import sendMessage, chunks, punish, getUserName
from config.config import DATABASE, PASSWORD, USER, TG_CHAT_ID, NEWSEASON_REWARDS, DAILY_TO, API, IMPLICIT_API, \
    GROUP_ID, TG_BACKUP_THREAD_ID, PHOTO_NOT_FOUND, YANDEX_TOKEN
from db import pool


async def backup() -> None:
    try:
        os.system('rm backup*.zip *.sql > /dev/null 2>&1')
        name = f"backup{datetime.now().strftime('%d-%m-%Y:%H:%M:%S')}.zip"
        db = f"{DATABASE}.sql"
        subprocess.run(f'PGPASSWORD="{PASSWORD}" pg_dump -h localhost -U {USER} -f {DATABASE}.sql {DATABASE}',
                       shell=True)
        with ZipFile(name, "a") as myzip:
            myzip.write(f"{db}")

        drive = yadisk.AsyncClient(token=YANDEX_TOKEN)
        async with drive:
            (await drive.upload(name, f'/StarManager/backups/{name}',
                                timeout=int(os.stat(name).st_size / 1000 / 128) * 1.5))
            file = await drive.get_download_link(f'/StarManager/backups/{name}')

        try:
            await tgbot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_BACKUP_THREAD_ID,
                                     text=f"<a href='{file}'>{name}</a>", parse_mode='HTML')
        except:
            traceback.print_exc()

        try:
            os.remove(name)
        except:
            traceback.print_exc()
        try:
            os.remove(db)
        except:
            traceback.print_exc()

        await sendMessage(DAILY_TO + 2000000000, 'backup: 100%')
    except Exception as e:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule backup:\n{e}')


async def updateInfo():
    try:
        await sendMessage(DAILY_TO + 2000000000, 'update_info: 0%')

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                users = chunks(await (await c.execute('select uid from usernames')).fetchall(), 999)
                chats = chunks(await (await c.execute('select chat_id from chatnames')).fetchall(), 99)
                groups = chunks(await (await c.execute('select group_id from groupnames')).fetchall(), 499)

                for i in users:
                    try:
                        names = await API.users.get(user_ids=[y[0] for y in i])
                        await c.executemany('update usernames set name = %s where uid=%s',
                                            [(f"{name.first_name} {name.last_name}", name.id) for name in names])
                    except:
                        pass

                for i in chats:
                    try:
                        chatnames = await API.messages.get_conversations_by_id(peer_ids=[2000000000 + y[0] for y in i])
                        await c.executemany(
                            'update chatnames set name = %s where chat_id=%s',
                            [(chat.chat_settings.title, chat.peer.id - 2000000000) for chat in chatnames.items])
                    except:
                        pass

                for i in groups:
                    try:
                        names = await API.groups.get_by_id(group_ids=[y[0] for y in i])
                        await c.executemany('update groupnames set name = %s where group_id=%s',
                                            [(name.name, -abs(name.id)) for name in names.groups])
                    except:
                        pass

                for i in await (await c.execute('select chat_id from publicchatssettings where last_update>%s',
                                                (int(time.time()) - 43200,))).fetchall():
                    try:
                        link = (await API.messages.get_invite_link(peer_id=2000000000 + i[0])).link
                        preview = await IMPLICIT_API.messages.get_chat_preview(link=link)
                        photo = PHOTO_NOT_FOUND
                        if preview.preview and preview.preview.photo:
                            if preview.preview.photo.photo_200:
                                photo = preview.preview.photo.photo_200
                            if preview.preview.photo.photo_100:
                                photo = preview.preview.photo.photo_100
                            if preview.preview.photo.photo_50:
                                photo = preview.preview.photo.photo_50
                        await c.execute(
                            'update publicchatssettings set link = %s, photo = %s, name = %s, members = %s, '
                            'last_update = %s where chat_id=%s',
                            (link, photo, preview.preview.title, preview.preview.members_count, int(time.time()), i[0]))
                    except:
                        await c.execute('delete from publicchatssettings where chat_id=%s', (i[0],))
                        await c.execute('delete from publicchats where chat_id=%s', (i[0],))
                    await asyncio.sleep(0.2)

                await conn.commit()
        await sendMessage(DAILY_TO + 2000000000, 'update_info: 100%')
    except Exception as e:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule update_info:\n{e}')


async def reboot():
    try:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('insert into reboots (chat_id, time, sended) VALUES (%s, %s, false)',
                                (DAILY_TO + 2000000000, int(time.time())))
                await c.execute('delete from messagesstatistics')
                await c.execute('delete from middlewaresstatistics')
                await conn.commit()
        await (await pool()).close()
        os.system('sudo reboot')
        await sendMessage(DAILY_TO + 2000000000, 'reboot: 100%')
    except Exception as e:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule reboot:\n{e}')


async def everyminute():
    try:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('delete from antispammessages where time<%s', (int(time.time() - 60),))
                await c.execute('delete from speccommandscooldown where time<%s', (int(time.time() - 10),))
                await c.execute('update xp set xp=0 where xp<0')
                await c.execute('delete from premium where time<%s', (int(time.time()),))
                unique = []
                for cp in await (await c.execute(
                        'select uid, chat_id from captcha where exptime<%s', (int(time.time()),))).fetchall():
                    try:
                        if cp in unique:
                            continue
                        if (await c.execute('delete from typequeue where chat_id=%s and uid=%s and type=\'captcha\'',
                                            (cp[1], cp[0]))).rowcount:
                            unique.append(cp)
                            s = await (await c.execute(
                                'select id, punishment from settings where chat_id=%s and setting=\'captcha\'', (cp[1],)
                            )).fetchone()
                            await punish(cp[0], cp[1], s[0])
                            await sendMessage(
                                cp[1] + 2000000000, messages.captcha_punish(cp[0], await getUserName(cp[0]), s[1]))
                    except:
                        await sendMessage(DAILY_TO + 2000000000, f'e from everyminute:\n' + traceback.format_exc())
                await c.execute('delete from captcha where exptime<%s', (int(time.time()),))
                await conn.commit()
    except:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from scheduler:\n' + traceback.format_exc())


async def run_notifications():
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            for i in await (await c.execute('select id, chat_id, tag, every, time, name, text '
                                            'from notifications where status=1 and every != -1')).fetchall():
                try:
                    if i[4] >= time.time():
                        continue
                    call = False
                    if i[2] == 1:
                        call = True
                    elif i[2] == 2:
                        try:
                            members = await API.messages.get_conversation_members(i[1] + 2000000000)
                            call = ''.join(
                                [f"[id{y.member_id}|\u200b\u206c]" for y in members.items if y.member_id > 0])
                        except:
                            pass
                    elif i[2] == 3:
                        ac = await c.execute('select uid from accesslvl where chat_id=%s and access_level>0 and uid>0',
                                             (i[1],))
                        call = ''.join([f"[id{y[0]}|\u200b\u206c]" for y in await ac.fetchall()])
                    else:
                        ac = await c.execute('select uid from accesslvl where chat_id=%s and access_level>0 and uid>0',
                                             (i[1],))
                        chat = [y[0] for y in await ac.fetchall()]
                        try:
                            members = await API.messages.get_conversation_members(i[1] + 2000000000)
                            call = ''.join([f"[id{y.member_id}|\u200b\u206c]" for y in members.items
                                            if y.member_id > 0 and y.member_id not in chat])
                        except:
                            pass
                    if call:
                        if not await sendMessage(i[1] + 2000000000, messages.send_notification(i[6], call)):
                            await sendMessage(i[1] + 2000000000, messages.notification_too_long_text(i[5]))
                    await c.execute('update notifications set status = %s, time = %s where id=%s',
                                    (0 if not i[3] else 1, int(i[4] + (i[3] * 60)) if i[3] else i[4], i[0]))
                except:
                    if i[1] == 34356:
                        traceback.print_exc()
                    pass
            await conn.commit()


async def run_nightmode_notifications():
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            for i in await (await c.execute('select chat_id, value2 from settings where setting=\'nightmode\' and '
                                            'pos=true and value2 is not null')).fetchall():
                args = i[1].split('-')
                now = datetime.now()
                start = datetime.strptime(args[0], '%H:%M').replace(year=2024)
                end = datetime.strptime(args[1], '%H:%M').replace(year=2024)
                if now.hour == start.hour and now.minute == start.minute:
                    await sendMessage(i[0] + 2000000000,
                                      messages.nightmode_start(start.strftime('%H:%M'), end.strftime('%H:%M')))
                elif now.hour == end.hour and now.minute == end.minute:
                    await sendMessage(i[0] + 2000000000, messages.nightmode_end())


async def run():
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    logger.info('loading tasks')
    aiocron.crontab('* * * * * 5', func=run_notifications, loop=loop)
    aiocron.crontab('* * * * * 5', func=run_nightmode_notifications, loop=loop)
    aiocron.crontab('*/1 * * * *', func=everyminute, loop=loop)
    aiocron.crontab('0 6/12 * * *', func=backup, loop=loop)
    aiocron.crontab('0 1/3 * * *', func=updateInfo, loop=loop)
    aiocron.crontab('50 23 * * *', func=reboot, loop=loop)
