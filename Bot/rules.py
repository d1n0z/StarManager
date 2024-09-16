from vkbottle import ABCRule
from vkbottle.bot import Message
from vkbottle_types.events import MessageNew

from Bot.checkers import getUserPrefixes
from Bot.utils import addDailyTask, getUserPremium
from config.config import PM_COMMANDS, MAIN_DEVS


class SearchCMD(ABCRule[Message]):
    def __init__(self, cmd: str):
        self.cmd = cmd

    async def check(self, event: Message) -> bool:
        if event.out == self.cmd:
            if event.from_id > 0:
                await addDailyTask(event.from_id, 'cmds')
            return True
        return False


class SearchPMCMD(ABCRule[Message]):
    def __init__(self, cmd: str):
        self.cmd = cmd

    async def check(self, event: MessageNew) -> bool:
        message = event.object.message
        if message.peer_id > 2000000000:
            return False
        text = message.text.lower().split()[0]
        for i in await getUserPrefixes(await getUserPremium(message.from_id), message.from_id):
            if not text.startswith(i):
                continue
            cmd = text.replace(i, '')
            for y in PM_COMMANDS:
                if cmd != y:
                    continue
                return self.cmd == cmd
        return False


class SearchPayloadCMD(ABCRule[Message]):
    def __init__(self, cmds: list = None):
        if cmds is None:
            cmds = []
        self.cmds = cmds

    async def check(self, event: Message) -> bool:
        cmd = event.payload['cmd']
        if cmd in self.cmds:
            return True
        return False
