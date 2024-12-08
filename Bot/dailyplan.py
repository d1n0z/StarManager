import calendar
import os
import subprocess
import threading
import time
import traceback
from time import sleep
from datetime import datetime
from zipfile import ZipFile

import schedule
import messages

from Bot.megadrive import mega_drive
from Bot.tgbot import getTGBot
from config.config import DATABASE, PASSWORD, USER, TG_CHAT_ID, REPORT_TO, NEWSEASON_REWARDS, GROUP_ID, \
    TASKS_DAILY, PREMIUM_TASKS_DAILY, VK_API_SESSION, VK_API_IMPLICIT_SESSION, DAILY_TO
from db import UserNames, ChatNames, GroupNames, Premium, Reboot, XP, TasksDaily, TasksWeekly


def backup() -> None:
    try:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'backup: 0%',
            'random_id': 0
        })

        os.system('rm backup*.zip *.sql')
        name = f"backup{datetime.now().strftime('%d-%m-%Y:%H:%M:%S')}.zip"
        db = f"{DATABASE}.sql"

        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'backup: (creating dumps) 10%',
            'random_id': 0
        })
        subprocess.run(f'PGPASSWORD="{PASSWORD}" pg_dump -h localhost -U {USER} -f {DATABASE}.sql {DATABASE}',
                       shell=True)

        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'backup: (creating zip) 40%',
            'random_id': 0
        })
        with ZipFile(name, "a") as myzip:
            myzip.write(f"{db}")

        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'backup: (uploading to Mega) 50%',
            'random_id': 0
        })
        drive = mega_drive()
        file = drive.upload(name)

        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'backup: (sending to Telegram) 80%',
            'random_id': 0
        })
        try:
            bot = getTGBot()
            bot.send_message(
                chat_id=TG_CHAT_ID,
                text=f"<a href='{drive.get_upload_link(file)}'>{name}</a>",
                parse_mode='HTML'
            )
        except:
            traceback.print_exc()

        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'backup: (deleting dumps) 90%',
            'random_id': 0
        })
        try:
            os.remove(name)
        except:
            traceback.print_exc()
        try:
            os.remove(db)
        except:
            traceback.print_exc()
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'backup: 100%',
            'random_id': 0
        })
    except Exception as e:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': f'e from schedule backup:\n{e}',
            'random_id': 0
        })


def resetPremium():
    try:
        Premium.delete().where(Premium.time < time.time()).execute()
    except Exception as e:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': f'e from schedule resetPremium:\n{e}',
            'random_id': 0
        })


def reboot():
    try:
        Reboot.create(chat_id=REPORT_TO, time=time.time(), sended=0).save()
        os.system('sudo reboot')
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'reboot: 100%',
            'random_id': 0
        })
    except Exception as e:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': f'e from schedule reboot:\n{e}',
            'random_id': 0
        })


def update_names_j():
    threading.Thread(target=update_names).start()


def update_names():
    try:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'update_names: (users) 0%',
            'random_id': 0
        })
        usernames = [[]]
        dbusers = {}
        for i in UserNames.select().iterator():
            dbusers[i.uid] = i
            usernames[-1].append(str(i.uid))
            if len(usernames[-1]) >= 999:
                usernames.append([])

        for i in usernames:
            try:
                names = VK_API_SESSION.method('users.get', {'user_ids': ','.join(i)})
                for name in names:
                    user = dbusers.get(name['id'])
                    name = f"{name['first_name']} {name['last_name']}"
                    if user.name != name:
                        user.name = name
                        user.save()
            except:
                traceback.print_exc()

        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'update_names: (chats) 33%',
            'random_id': 0
        })
        for i in ChatNames.select().iterator():
            try:
                chatname = VK_API_SESSION.method('messages.getConversationsById', {'peer_ids': 2000000000 + i.chat_id})
                chatname = chatname['items'][0]['chat_settings']['title']
                if chatname != i.name:
                    i.name = chatname
                    i.save()
            except:
                traceback.print_exc()

        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'update_names: (groups) 66%',
            'random_id': 0
        })
        for i in GroupNames.select().iterator():
            try:
                name = VK_API_SESSION.method('groups.getById', {'group_ids': i.group_id})['groups'][0]['name']
                if name != i.name:
                    i.name = name
                    i.save()
            except:
                traceback.print_exc()

        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': 'update_names: 100%',
            'random_id': 0
        })
    except Exception as e:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': f'e from schedule update_names:\n{e}',
            'random_id': 0
        })


def everyday():
    try:
        try:
            VK_API_SESSION.method('messages.send', {
                'chat_id': DAILY_TO,
                'message': 'daily task reset: 0%',
                'random_id': 0
            })
        except:
            print('task started, exception')
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
        try:
            VK_API_SESSION.method('messages.send', {
                'chat_id': DAILY_TO,
                'message': 'daily task reset: 100%',
                'random_id': 0
            })
        except:
            print('task ended, exception')
        if datetime.now().weekday() == 0:
            TasksWeekly.delete().execute()
            VK_API_SESSION.method('messages.send', {
                'chat_id': DAILY_TO,
                'message': 'weekly tasks reset: 100%',
                'random_id': 0
            })
        names = {}
        if datetime.now().day == 1:
            top = XP.select().where(XP.uid > 1).order_by(XP.xp.desc()).limit(10)
            for k, i in enumerate(top):
                p = Premium.get_or_create(uid=i.uid, defaults={'time': 0})[0]
                if p.time < datetime.now().timestamp():
                    p.time = datetime.now().timestamp() + (NEWSEASON_REWARDS[k] * 86400)
                else:
                    p.time += NEWSEASON_REWARDS[k] * 86400
                p.save()
                name = VK_API_SESSION.method('users.get', {'user_ids': i.uid})[0]
                name = f'{name["first_name"]} {name["last_name"]}'
                names[f'{i.uid}'] = name
                try:
                    msg = messages.newseason_top(k + 1, NEWSEASON_REWARDS[k]),
                    VK_API_SESSION.method('messages.send', {
                        'user_id': i.uid,
                        'message': msg,
                        'random_id': 0
                    })
                except:
                    pass
            XP.update(xp=0).execute()
            season_start = datetime.now().strftime('%d.%m.%Y')
            ld = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
            season_end = datetime.now().replace(day=ld).strftime('%d.%m.%Y')
            msg = messages.newseason_post(
                [(i.uid, names[i.uid],
                  (i.xp - 100) // 200 + 2 if i.xp > 100 else 1) for i in top], season_start, season_end
            )
            VK_API_IMPLICIT_SESSION.method('wall.post', {
                'owner_id': -GROUP_ID,
                'from_group': 1,
                'guid': 1,
                'message': msg
            })
    except Exception as e:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': f'e from schedule everyday:\n{e}',
            'random_id': 0
        })


def scheduler():
    try:
        scheduler = schedule.Scheduler()
        scheduler.every(3).hours.do(update_names_j)
        scheduler.every().hour.do(resetPremium)
        scheduler.every().day.at("00:00").do(everyday)
        scheduler.every().day.at("03:00").do(backup)
        scheduler.every().day.at("09:00").do(backup)
        scheduler.every().day.at("15:00").do(backup)
        scheduler.every().day.at("21:00").do(backup)
        scheduler.every().day.at("23:50").do(reboot)
        while True:
            scheduler.run_pending()
            time.sleep(1)
    except Exception as e:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': f'e from schedule scheduler:\n{e}',
            'random_id': 0
        })
