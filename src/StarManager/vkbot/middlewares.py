import traceback

from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from StarManager.vkbot.checkers import checkCMD


class CommandMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        try:
            cmd = await checkCMD(self.event, self.event.chat_id, returncmd=True)
            self.event.out = cmd  # type: ignore may god forgive me
        except Exception:
            traceback.print_exc()
            raise
