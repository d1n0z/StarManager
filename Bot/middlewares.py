from datetime import datetime

from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from Bot.checkers import checkCMD
from db import pool


class CommandMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        timestart = datetime.now()

        cmd = await checkCMD(self.event, self.event.chat_id, returncmd=True)
        self.event.out = cmd
        if cmd:
            self.event.geo = datetime.now()

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('insert into middlewaresstatistics (timestart, timeend) values (%s, %s)',
                                (timestart, datetime.now()))
                await conn.commit()

    async def post(self):
        if not isinstance(self.event.geo, tuple):
            return
        if self.handlers:
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    await c.execute('insert into commandsstatistics (cmd, timestart, timeend) values (%s, %s, %s)',
                                    (self.event.out, self.event.geo, datetime.now()))
                    await conn.commit()
