import asyncio
import threading

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from Bot.checkers import checkCMD
from Bot.rules import SearchCMD
from Bot.utils import setUserAccessLevel
from config.config import DEVS

bl = BotLabeler()


@bl.chat_message(SearchCMD('test'))
async def test_handler(message: Message):
    chat_id = message.peer_id - 2000000000
    if await checkCMD(message, chat_id):
        await message.reply(f'💬 ID данной беседы : {chat_id}')


@bl.chat_message(SearchCMD('getdev'))
async def getdev_handler(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if await checkCMD(message, chat_id):
        if uid in DEVS:
            await setUserAccessLevel(uid, chat_id, 8)


@bl.chat_message(SearchCMD('backup'))
async def backup_handler(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    if await checkCMD(message, chat_id):
        if uid in DEVS:
            from Bot.scheduler import backup
            asyncio.run(backup())
