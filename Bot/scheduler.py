import asyncio
import calendar
import os
import subprocess
import time
import traceback
from datetime import datetime
from zipfile import ZipFile

import aiocron

import messages
from Bot.megadrive import mega_drive
from Bot.tgbot import getTGBot
from Bot.utils import sendMessage, chunks
from config.config import DATABASE, PASSWORD, USER, TG_CHAT_ID, REPORT_TO, NEWSEASON_REWARDS, TASKS_DAILY, \
    PREMIUM_TASKS_DAILY, DAILY_TO, API, IMPLICIT_API, GROUP_ID
from db import UserNames, ChatNames, GroupNames, Premium, Reboot, XP, TasksDaily, TasksWeekly, AntispamMessages, \
    Settings, SpecCommandsCooldown


async def resetPremium():
    try:
        Premium.delete().where(Premium.time < time.time()).execute()
        await sendMessage(DAILY_TO + 2000000000, 'reset premium: 100%')
    except Exception as e:
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule resetPremium:\n{e}')


async def deleteTempdataDB():
    try:
        AntispamMessages.delete().where(AntispamMessages.time < time.time() - 60).execute()
        SpecCommandsCooldown.delete().where(SpecCommandsCooldown.time < time.time() - 10).execute()
    except Exception as e:
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule resetAntispamMessages:\n{e}')


async def dailyTasks():
    try:
        buids = []
        for i in TasksDaily.select():
            if i.uid not in buids:
                prem = Premium.get_or_none(Premium.uid == i.uid)
                prem = prem.time if prem is not None else 0
                tasks = [TasksDaily.get_or_none(TasksDaily.uid == i.uid, TasksDaily.task == 'sendmsgs')]
                tasks[0] = tasks[0].count if tasks[0] is not None else 0
                tasks.append(TasksDaily.get_or_none(TasksDaily.uid == i.uid, TasksDaily.task == 'sendvoice'))
                tasks[1] = tasks[1].count if tasks[1] is not None else 0
                tasks.append(TasksDaily.get_or_none(TasksDaily.uid == i.uid, TasksDaily.task == 'duelwin'))
                tasks[2] = tasks[2].count if tasks[2] is not None else 0
                tasks.append(TasksDaily.get_or_none(TasksDaily.uid == i.uid, TasksDaily.task == 'cmds'))
                tasks[3] = tasks[3].count if tasks[3] is not None else 0
                tasks.append(TasksDaily.get_or_none(TasksDaily.uid == i.uid, TasksDaily.task == 'stickers'))
                tasks[4] = tasks[4].count if tasks[4] is not None else 0
                count = [tasks[0] >= TASKS_DAILY["sendmsgs"], tasks[1] >= TASKS_DAILY["sendvoice"],
                         tasks[2] >= TASKS_DAILY["duelwin"]].count(True)
                countrange = 3
                if prem:
                    countrange += 2
                    count += [tasks[3] >= PREMIUM_TASKS_DAILY["cmds"],
                              tasks[4] >= PREMIUM_TASKS_DAILY["stickers"]].count(True)
                if count >= countrange:
                    dt = TasksWeekly.get_or_create(uid=i.uid, task='dailytask')[0]
                    dt.count += 1
                    dt.save()
                buids.append(i.uid)
        TasksDaily.delete().execute()
        await sendMessage(DAILY_TO + 2000000000, 'daily tasks reset: 100%')
    except Exception as e:
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule dailyTasks:\n{e}')


async def weeklyTasks():
    try:
        TasksWeekly.delete().execute()
        await sendMessage(DAILY_TO + 2000000000, 'weekly tasks reset: 100%')
    except Exception as e:
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule everyday:\n{e}')


async def backup() -> None:
    try:
        os.system('rm backup*.zip *.sql')
        name = f"backup{datetime.now().strftime('%d-%m-%Y:%H:%M:%S')}.zip"
        db = f"{DATABASE}.sql"
        subprocess.run(f'PGPASSWORD="{PASSWORD}" pg_dump -h localhost -U {USER} -f {DATABASE}.sql {DATABASE}',
                       shell=True)
        with ZipFile(name, "a") as myzip:
            myzip.write(f"{db}")

        drive = mega_drive()
        file = drive.upload(name)

        try:
            bot = getTGBot()
            bot.send_message(chat_id=TG_CHAT_ID, text=f"<a href='{drive.get_upload_link(file)}'>{name}</a>",
                             parse_mode='HTML')
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
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule backup:\n{e}')


async def updateNames():
    try:
        await sendMessage(DAILY_TO + 2000000000, 'update_names: 0%')

        users = chunks(UserNames.select(), 999)
        chats = chunks(ChatNames.select(), 99)
        groups = chunks(GroupNames.select(), 499)

        for i in users:
            try:
                names = await API.users.get(user_ids=','.join(str(y.uid) for y in i))
                for name in names:
                    user = UserNames.get(UserNames.uid == name.id)
                    name = f"{name.first_name} {name.last_name}"
                    if user.name != name:
                        user.name = name
                        user.save()
            except:
                traceback.print_exc()

        for i in chats:
            try:
                chatnames = await API.messages.get_conversations_by_id(
                    peer_ids=','.join(str(2000000000 + y.chat_id) for y in i))
                for chatname in chatnames.items:
                    chat = ChatNames.get(ChatNames.chat_id == chatname.peer.id - 2000000000)
                    chatname = chatname.chat_settings.title
                    if chatname != chat.name:
                        chat.name = chatname
                        chat.save()
            except:
                traceback.print_exc()

        for i in groups:
            try:
                names = await API.groups.get_by_id(group_ids=','.join(str(y.group_id) for y in i))
                for name in names:
                    group = GroupNames.get(GroupNames.group_id == -name.id)
                    name = name.name
                    if name != group.name:
                        group.name = name
                        group.save()
            except:
                traceback.print_exc()

        await sendMessage(DAILY_TO + 2000000000, 'update_names: 100%')
    except Exception as e:
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule update_names:\n{e}')


async def reboot():
    try:
        Reboot.create(chat_id=REPORT_TO, time=time.time(), sended=0).save()
        os.system('sudo reboot')
        await sendMessage(DAILY_TO + 2000000000, 'reboot: 100%')
    except Exception as e:
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule reboot:\n{e}')


async def new_season():
    try:
        await sendMessage(DAILY_TO + 2000000000, '@all new_season: 0%')
        top = XP.select().where(XP.uid > 1).order_by(XP.xp.desc()).limit(10)
        if len(top) != 10:
            await sendMessage(DAILY_TO + 2000000000, f'@all INCORRECT top LENGTH!\nLENGHT: {len(top)}')
            return
        for k, i in enumerate(top):
            p = Premium.get_or_create(uid=i.uid, defaults={'time': 0})[0]
            if p.time < datetime.now().timestamp():
                p.time = datetime.now().timestamp()
            p.time += NEWSEASON_REWARDS[k] * 86400
            p.save()
            try:
                msg = messages.newseason_top(k + 1, NEWSEASON_REWARDS[k])
                await sendMessage(i.uid, msg)
            except:
                await sendMessage(DAILY_TO + 2000000000, f'FAILED TO SEND MESSAGE TO [id{i.uid}|USER]!\n'
                                                         f'REWARD STILL RECEIVED!\n ERROR:\n' + traceback.format_exc())
        season_start = datetime.now().strftime('%d.%m.%Y')
        now = datetime.now()
        ld = calendar.monthrange(datetime.now().year, now.month)[1]
        season_end = now.replace(day=ld).strftime('%d.%m.%Y')
        try:
            msg = await messages.newseason_post(top, season_start, season_end)
        except:
            await sendMessage(DAILY_TO + 2000000000, f'@all POST MESSAGE CREATING FAILURE!\nERROR:\n' +
                              traceback.format_exc())
            return
        try:
            await IMPLICIT_API.wall.post(owner_id=-GROUP_ID, from_group=1, guid=1, message=msg)
        except:
            await sendMessage(DAILY_TO + 2000000000, f'@all POST FAILURE!\nPOST MESSAGE: {msg}\nERROR:\n' +
                              traceback.format_exc())
            return
        XP.update(xp=0).execute()
        await sendMessage(DAILY_TO + 2000000000, '@all new_season: 100%')
    except:
        await sendMessage(DAILY_TO + 2000000000, f'e from scheduler:\n' + traceback.format_exc())


async def everyminute():
    try:
        s = Settings.select().where(Settings.setting == 'nightmode', Settings.value2.is_null(False))
        for i in s:
            args = i.value2.split('-')
            now = datetime.now()
            start = datetime.strptime(args[0], '%H:%M').replace(year=2024)
            end = datetime.strptime(args[1], '%H:%M').replace(year=2024)
            if now.hour == start.hour and now.minute == start.minute:
                await sendMessage(i.chat_id + 2000000000, messages.nightmode_start(f'{start.hour}:{start.minute}',
                                                                                   f'{end.hour}:{end.minute}'))
            elif now.hour == end.hour and now.minute == end.minute:
                await sendMessage(i.chat_id + 2000000000, messages.nightmode_end())
        print(f'everyminute: 100% ({datetime.now().strftime("%H:%M:%S")})')
    except:
        await sendMessage(DAILY_TO + 2000000000, f'e from scheduler:\n' + traceback.format_exc())


async def run():
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    aiocron.crontab('* * * * * */5', func=deleteTempdataDB, loop=loop)
    aiocron.crontab('*/1 * * * *', func=everyminute, loop=loop)
    aiocron.crontab('0 * * * *', func=resetPremium, loop=loop)
    aiocron.crontab('0 0 * * *', func=dailyTasks, loop=loop)
    aiocron.crontab('0 0 * * 1', func=weeklyTasks, loop=loop)
    aiocron.crontab('0 3/6 * * *', func=backup, loop=loop)
    aiocron.crontab('0 1/3 * * *', func=updateNames, loop=loop)
    aiocron.crontab('50 23 * * *', func=reboot, loop=loop)
    aiocron.crontab('0 0 1 * *', func=new_season, loop=loop)
