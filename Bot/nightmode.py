import traceback
from datetime import datetime
from time import sleep

import messages
from config.config import VK_API_SESSION
from db import Settings


def run_nightmode_notifications():
    while True:
        if datetime.now().second == 0:
            s = Settings.select().where(Settings.setting == 'nightmode', Settings.pos == 1,
                                        Settings.value2.is_null(False))
            for i in s:
                args = i.value2.split('-')
                now = datetime.now()
                start = datetime.strptime(args[0], '%H:%M').replace(year=2024)
                end = datetime.strptime(args[1], '%H:%M').replace(year=2024)
                if now.hour == start.hour and now.minute == start.minute:
                    try:
                        VK_API_SESSION.method('messages.send', {
                            'chat_id': i.chat_id,
                            'message': messages.nightmode_start(start.strftime('%H:%M'), end.strftime('%H:%M')),
                            'random_id': 0
                        })
                    except:
                        traceback.print_exc()
                elif now.hour == end.hour and now.minute == end.minute:
                    try:
                        VK_API_SESSION.method('messages.send', {
                            'chat_id': i.chat_id,
                            'message': messages.nightmode_end(),
                            'random_id': 0
                        })
                    except:
                        traceback.print_exc()
            sleep(1)
        sleep(0.5)
