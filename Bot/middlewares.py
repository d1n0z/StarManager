import traceback
from datetime import datetime

from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from Bot.checkers import checkCMD
from db import pool


class CommandMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        try:
            timestart = datetime.now()

            cmd = await checkCMD(self.event, self.event.chat_id, returncmd=True)
            self.event.out = cmd  # god forgive me
            if cmd:
                self.event.geo = datetime.now()

            async with (await pool()).acquire() as conn:
                if not isinstance(cmd, bool):
                    await conn.execute('insert into cmdsusage (uid, cmd) values ($1, $2)', self.event.from_id, cmd)
                await conn.execute('insert into middlewaresstatistics (timestart, timeend) values ($1, $2)',
                                   timestart, datetime.now())
        except:
            traceback.print_exc()
            raise

    async def post(self):
        if not isinstance(self.event.geo, tuple):
            return
        if self.handlers:
            async with (await pool()).acquire() as conn:
                await conn.execute('insert into commandsstatistics (cmd, timestart, timeend) values ($1, $2, $3)',
                                   self.event.out, self.event.geo, datetime.now())
