from vkbottle import ABCRule
from vkbottle.bot import Message, MessageEvent
from vkbottle_types.events.bot_events import MessageNew

from Bot.utils import getUserPremium, sendMessageEventAnswer, getUserPrefixes
from config.config import PM_COMMANDS


class SearchCMD(ABCRule[Message]):
    def __init__(self, cmd: str):
        self.cmd = cmd

    async def check(self, event: Message) -> bool:
        if event.out == self.cmd:
            return True
        return False


class SearchPMCMD(ABCRule[Message]):
    def __init__(self, cmd: str):
        self.cmd = cmd

    async def check(self, event: MessageNew) -> bool:
        message = event.object.message
        if message.peer_id > 2000000000 or not message.text:
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
    def __init__(self, cmds: list = None, answer: bool = True, checksender: bool = True):
        self.cmds = cmds or []
        self.answer = answer
        self.checksender = checksender

    async def check(self, event: MessageEvent) -> bool:
        if event.payload['cmd'] in self.cmds:
            if self.answer:
                await sendMessageEventAnswer(event.event_id, event.user_id, event.peer_id)
            if self.checksender:
                sender = event.payload['uid'] if 'uid' in event.payload else event.user_id
                if sender != event.user_id:
                    return False
            return True
        return False
