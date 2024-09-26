from datetime import datetime

from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from Bot.checkers import checkCMD
from db import CommandsStatistics, MiddlewaresStatistics


class CommandMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        m = MiddlewaresStatistics.create(timestart=datetime.now())
        cmd = await checkCMD(self.event, self.event.chat_id, returncmd=True)
        self.event.out = cmd
        if cmd:
            cs = CommandsStatistics.create(cmd=cmd, timestart=datetime.now())
            self.event.geo = cs
        m.timeend = datetime.now()
        m.save()

    async def post(self):
        if not isinstance(self.event.geo, CommandsStatistics):
            return
        cs: CommandsStatistics = self.event.geo  # noqa
        if self.handlers:
            cs.timeend = datetime.now()
            cs.save()
        else:
            cs.delete_instance()
