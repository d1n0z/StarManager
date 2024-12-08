from datetime import datetime

import messages
from Bot.utils import sendMessage
from db import Settings


async def run_nightmode_notifications():
    for i in Settings.select().where(
            Settings.setting == 'nightmode', Settings.pos == 1, Settings.value2.is_null(False)):
        args = i.value2.split('-')
        now = datetime.now()
        start = datetime.strptime(args[0], '%H:%M').replace(year=2024)
        end = datetime.strptime(args[1], '%H:%M').replace(year=2024)
        if now.hour == start.hour and now.minute == start.minute:
            await sendMessage(i.chat_id + 2000000000,
                              messages.nightmode_start(start.strftime('%H:%M'), end.strftime('%H:%M')))
        elif now.hour == end.hour and now.minute == end.minute:
            await sendMessage(i.chat_id + 2000000000, messages.nightmode_end())
