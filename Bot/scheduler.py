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
from Bot.utils import sendMessage, getUserName, chunks
from config.config import DATABASE, PASSWORD, USER, TG_CHAT_ID, REPORT_TO, NEWSEASON_REWARDS, TASKS_DAILY, \
    PREMIUM_TASKS_DAILY, DAILY_TO, API, IMPLICIT_API, GROUP_ID
from db import UserNames, ChatNames, GroupNames, Premium, Reboot, XP, TasksDaily, TasksWeekly


async def resetPremium():
    try:
        Premium.delete().where(Premium.time < time.time()).execute()
        await sendMessage(DAILY_TO + 2000000000, 'reset premium: 100%')
    except Exception as e:
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule resetPremium:\n{e}')


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
        await sendMessage(DAILY_TO + 2000000000, 'new_season: 0%\n@all')
        await asyncio.sleep(30)
        top = XP.select().where(XP.uid > 1).order_by(XP.xp.desc()).limit(10)
        for k, i in enumerate(top):
            p = Premium.get_or_create(uid=i.uid, defaults={'time': 0})[0]
            if p.time < datetime.now().timestamp():
                p.time = datetime.now().timestamp() + (NEWSEASON_REWARDS[k] * 86400)
            else:
                p.time += NEWSEASON_REWARDS[k] * 86400
            p.save()
            try:
                msg = messages.newseason_top(k + 1, NEWSEASON_REWARDS[k]),
                await sendMessage(i.uid, msg)
            except:
                pass
        XP.update(xp=0).execute()
        season_start = datetime.now().strftime('%d.%m.%Y')
        ld = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
        season_end = datetime.now().replace(day=ld).strftime('%d.%m.%Y')
        msg = messages.newseason_post(
            [(i.uid, await getUserName(i.uid), (i.xp - 100) // 200 + 2 if i.xp > 100 else 1) for i in top],
            season_start, season_end)
        await IMPLICIT_API.wall.post(owner_id=-GROUP_ID, from_group=1, guid=1, message=msg)
        await sendMessage(DAILY_TO + 2000000000, 'new_season: 100%')
    except Exception as e:
        await sendMessage(DAILY_TO + 2000000000, f'e from schedule everyday:\n{e}')


def run(loop):
    asyncio.set_event_loop(loop)
    aiocron.crontab('0 * * * *', func=resetPremium, loop=loop)
    aiocron.crontab('0 0 * * *', func=dailyTasks, loop=loop)
    aiocron.crontab('0 0 * * 1', func=weeklyTasks, loop=loop)
    aiocron.crontab('0 3/6 * * *', func=backup, loop=loop)
    aiocron.crontab('0 1/3 * * *', func=updateNames, loop=loop)
    aiocron.crontab('50 23 * * *', func=reboot, loop=loop)
    aiocron.crontab('0 0 1 * *', func=new_season, loop=loop)
