from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from Bot.checkers import checkCMD


class CommandMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        cmd = await checkCMD(self.event, self.event.chat_id, returncmd=True)
        self.event.out = cmd
