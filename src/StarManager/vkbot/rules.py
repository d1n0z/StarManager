from vkbottle import ABCRule
from vkbottle.bot import Message, MessageEvent
from vkbottle_types.events.bot_events import MessageNew

from StarManager.core.utils import (
    get_user_premium,
    send_message_event_answer,
    get_user_prefixes,
)
from StarManager.core.config import settings


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
        if not message or message.peer_id > 2000000000 or not message.text:
            return False
        text = message.text.lower().split()[0]
        for i in await get_user_prefixes(
            await get_user_premium(message.from_id), message.from_id
        ):
            if not text.startswith(i):
                continue
            cmd = text.replace(i, "")
            for y in settings.commands.pm:
                if cmd != y:
                    continue
                return self.cmd == cmd
        return False


class SearchPayloadCMD(ABCRule[Message]):
    def __init__(
        self, cmds: list | None = None, answer: bool = True, checksender: bool = True
    ):
        self.cmds = cmds or []
        self.answer = answer
        self.checksender = checksender

    async def check(self, event: MessageEvent) -> bool:
        if event.payload and event.payload["cmd"] in self.cmds:
            if self.answer:
                await send_message_event_answer(
                    event.event_id, event.user_id, event.peer_id
                )
            if self.checksender:
                allowed = (
                    event.payload["uid"] if "uid" in event.payload else event.user_id
                )
                if isinstance(allowed, str) and str(event.user_id) not in allowed.split(','):
                    return False
                if isinstance(allowed, int) and allowed != event.user_id:
                    return False
            return True
        return False
