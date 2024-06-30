from vkbottle import ABCRule
from vkbottle.bot import Message

from Bot.utils import addDailyTask


class SearchCMD(ABCRule[Message]):
    def __init__(self, cmd: str):
        self.cmd = cmd

    async def check(self, event: Message) -> bool:
        if event.out == self.cmd:
            if event.from_id > 0:
                await addDailyTask(event.from_id, 'cmds')
            return True
        return False


class SearchPayloadCMD(ABCRule[Message]):
    def __init__(self, cmds: list = None):
        if cmds is None:
            cmds = []
        self.cmds = cmds

    async def check(self, event: Message) -> bool:
        try:
            cmd = event.payload['cmd']
            for i in self.cmds:
                if cmd == i:
                    return True
        except:
            pass
        return False
