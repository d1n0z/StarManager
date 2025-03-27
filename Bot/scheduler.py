import asyncio
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
from config.config import DATABASE, PASSWORD, USER, TG_CHAT_ID, DAILY_TO, api, TG_BACKUP_THREAD_ID, PHOTO_NOT_FOUND, \
    YANDEX_TOKEN, COMMANDS, vk_api_session, GROUP_ID, PATH
from db import smallpool as pool


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
    except Exception as e:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule backup:\n{e}')


async def updateInfo():
    try:
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                users = chunks(await conn.fetch('select uid from usernames'), 999)
                chats = chunks(await conn.fetch('select chat_id from chatnames'), 99)
                groups = chunks(await conn.fetch('select group_id from groupnames'), 499)

                for i in users:
                    try:
                        names = await api.users.get(user_ids=[y[0] for y in i])
                        await conn.executemany('update usernames set name = $1 where uid=$2',
                                               [(f"{name.first_name} {name.last_name}", name.id) for name in names])
                    except:
                        pass

                for i in chats:
                    try:
                        chatnames = await api.messages.get_conversations_by_id(peer_ids=[2000000000 + y[0] for y in i])
                        await conn.executemany(
                            'update chatnames set name = $1 where chat_id=$2',
                            [(chat.chat_settings.title, chat.peer.id - 2000000000) for chat in chatnames.items])
                    except:
                        pass

                for i in groups:
                    try:
                        names = await api.groups.get_by_id(group_ids=[y[0] for y in i])
                        await conn.executemany('update groupnames set name = $1 where group_id=$2',
                                               [(name.name, -abs(name.id)) for name in names.groups])
                    except:
                        pass

                for i in await conn.fetch(
                        'select chat_id from publicchats where isopen=true and not chat_id=ANY($1)',
                        [i[0] for i in await conn.fetch(
                            'select chat_id from publicchatssettings where last_update>$1', time.time() - 43200)]):
                    try:
                        link = vk_api_session.method(
                            'messages.getInviteLink', {'peer_id': 2000000000 + i[0], 'group_id': GROUP_ID})['link']
                        vkchat = vk_api_session.method(
                            'messages.getConversationsById', {'peer_ids': 2000000000 + i[0]})
                        if 'items' not in vkchat or not vkchat['items'] or 'chat_settings' not in vkchat['items'][0]:
                            continue
                        vkchat = vkchat['items'][0]['chat_settings']
                        photo = PHOTO_NOT_FOUND
                        if 'photo' in vkchat:
                            if 'photo_200' in vkchat['photo']:
                                photo = vkchat['photo']['photo_200']
                            elif 'photo_100' in vkchat['photo']:
                                photo = vkchat['photo']['photo_100']
                            elif 'photo_50' in vkchat['photo']:
                                photo = vkchat['photo']['photo_50']
                        if not await conn.fetchval(
                                'update publicchatssettings set link = $1, photo = $2, name = $3, members = $4, '
                                'last_update = $5 where chat_id=$6 returning 1', link, photo, vkchat['title'],
                                vkchat['members_count'], time.time(), i[0]):
                            await conn.execute('insert into publicchatssettings (chat_id, link, photo, name, members, '
                                               'last_update) values ($1, $2, $3, $4, $5, $6)', i[0], link, photo,
                                               vkchat['title'], vkchat['members_count'], time.time())
                    except:
                        await conn.execute('update publicchats set isopen=false where chat_id=$1', i[0])
                    await asyncio.sleep(0.2)
    except Exception as e:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule update_info:\n{e}')


async def reboot():
    try:
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute('insert into reboots (chat_id, time, sended) VALUES ($1, $2, false)',
                                   DAILY_TO + 2000000000, time.time())
                await conn.execute('delete from messagesstatistics')
                await conn.execute('delete from middlewaresstatistics')
        await (await pool()).close()
        os.system('sudo reboot')
    except Exception as e:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule reboot:\n{e}')


async def everyminute():
    try:
        os.system(f'find {PATH}' + 'media/temp/ -mtime +1 -exec rm {} \;')  # noqa
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                await conn.fetch('select state, count(*) from pg_stat_activity group by state')
                await conn.execute('delete from cmdnames where not cmd=ANY($1)', list(COMMANDS.keys()))
                await conn.execute('delete from antispammessages where time<$1', time.time() - 60)
                await conn.execute('delete from speccommandscooldown where time<$1', time.time() - 10)
                await conn.execute('update xp set xp=0 where xp<0')
                await conn.execute('delete from premium where time<$1', time.time())
                unique = []
                for cp in await conn.fetch('select uid, chat_id from captcha where exptime<$1', time.time()):
                    try:
                        if cp in unique:
                            continue
                        if await conn.fetchval('delete from typequeue where chat_id=$1 and uid=$2 and type=\'captcha\' '
                                               'returning 1', cp[1], cp[0]):
                            unique.append(cp)
                            s = await conn.fetchrow('select id, punishment from settings where chat_id=$1 and '
                                                    'setting=\'captcha\'', cp[1])
                            await punish(cp[0], cp[1], s[0])
                            await sendMessage(
                                cp[1] + 2000000000, messages.captcha_punish(cp[0], await getUserName(cp[0]), s[1]))
                    except:
                        await sendMessage(DAILY_TO + 2000000000, f'e from everyminute:\n' + traceback.format_exc())
                await conn.execute('delete from captcha where exptime<$1', time.time())
    except:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule everyminute:\n' + traceback.format_exc())


async def run_notifications():
    try:
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                for i in await conn.fetch('select id, chat_id, tag, every, time, name, text '
                                          'from notifications where status=1 and every != -1'):
                    try:
                        if await conn.fetchval(
                                "select exists(select 1 from blocked where uid=$1 and type='chat')", i[1]):
                            continue
                        if i[4] >= time.time():
                            continue
                        call = False
                        if i[2] == 1:
                            call = True
                        elif i[2] == 2:
                            try:
                                members = await api.messages.get_conversation_members(i[1] + 2000000000)
                                call = ''.join(
                                    [f"[id{y.member_id}|\u200b\u206c]" for y in members.items if y.member_id > 0])
                            except:
                                pass
                        elif i[2] == 3:
                            ac = await conn.fetch(
                                'select uid from accesslvl where chat_id=$1 and access_level>0 and uid>0', i[1])
                            call = ''.join([f"[id{y[0]}|\u200b\u206c]" for y in await ac])
                        else:
                            ac = await conn.fetch(
                                'select uid from accesslvl where chat_id=$1 and access_level>0 and uid>0', i[1])
                            chat = [y[0] for y in await ac]
                            try:
                                members = await api.messages.get_conversation_members(i[1] + 2000000000)
                                call = ''.join([f"[id{y.member_id}|\u200b\u206c]" for y in members.items
                                                if y.member_id > 0 and y.member_id not in chat])
                            except:
                                pass
                        if call:
                            if not await sendMessage(i[1] + 2000000000, messages.send_notification(i[6], call)):
                                await sendMessage(i[1] + 2000000000, messages.notification_too_long_text(i[5]))
                        await conn.execute('update notifications set status = $1, time = $2 where id=$3',
                                           0 if not i[3] else 1, int(i[4] + (i[3] * 60)) if i[3] else i[4], i[0])
                    except:
                        if i[1] == 34356:
                            traceback.print_exc()
                        pass
    except:
        traceback.print_exc()
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule run_notifications:\n' + traceback.format_exc())


async def run_nightmode_notifications():
    try:
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                for i in await conn.fetch('select chat_id, value2 from settings where setting=\'nightmode\' and '
                                          'pos=true and value2 is not null'):
                    if await conn.fetchval("select exists(select 1 from blocked where uid=$1 and type='chat')", i[0]):
                        continue
                    args = i[1].split('-')
                    now = datetime.now()
                    start = datetime.strptime(args[0], '%H:%M').replace(year=2024)
                    end = datetime.strptime(args[1], '%H:%M').replace(year=2024)
                    if now.hour == start.hour and now.minute == start.minute:
                        await sendMessage(i[0] + 2000000000,
                                          messages.nightmode_start(start.strftime('%H:%M'), end.strftime('%H:%M')))
                    elif now.hour == end.hour and now.minute == end.minute:
                        await sendMessage(i[0] + 2000000000, messages.nightmode_end())
    except:
        traceback.print_exc()
        await sendMessage(
            DAILY_TO + 2000000000, f'e from schedule run_nightmode_notifications:\n' + traceback.format_exc())


async def run():
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    logger.info('loading tasks')
    aiocron.crontab('* * * * * 15', func=run_notifications, loop=loop)
    aiocron.crontab('* * * * * 15', func=run_nightmode_notifications, loop=loop)
    aiocron.crontab('*/1 * * * *', func=everyminute, loop=loop)
    aiocron.crontab('0 6/12 * * *', func=backup, loop=loop)
    aiocron.crontab('0 1/3 * * *', func=updateInfo, loop=loop)
    # aiocron.crontab('50 23 * * *', func=reboot, loop=loop)
