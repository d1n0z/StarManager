import sys
import threading
import traceback

from loguru import logger
from vkbottle import Bot, GroupEventType, GroupTypes
from vkbottle.bot import MessageReactionEvent

from Bot.labelers import LABELERS
from Bot.comment_handlers import comment_handle
from Bot.like_handlers import like_handle
from Bot.message_handlers import message_handle
from Bot.middlewares import CommandMiddleware
from Bot.reaction_handlers import reaction_handle
from config.config import VK_TOKEN_GROUP, VK_API_SESSION
from db import Reboot


class VkBot:
    def __init__(self):
        try:
            self.bot = Bot(VK_TOKEN_GROUP)
        except Exception as e:
            print(e)

    def run(self):
        logger.remove()
        logger.add(sys.stderr, level='INFO')

        from Bot.dailyplan import scheduler
        threading.Thread(target=scheduler).start()

        from Bot.notifications import run_notifications
        threading.Thread(target=run_notifications).start()

        # elif event.type == 'message_reaction_event':
        #     threading.Thread(target=reaction_handle, args=(self, event,)).start()

        @self.bot.on.raw_event(GroupEventType.MESSAGE_REACTION_EVENT, dataclass=MessageReactionEvent)
        async def start(event: MessageReactionEvent):
            await reaction_handle(event)

        @self.bot.on.raw_event(GroupEventType.MESSAGE_NEW, dataclass=GroupTypes.MessageNew)
        async def new_message(event: GroupTypes.MessageNew):
            await message_handle(event)

        @self.bot.on.raw_event(GroupEventType.WALL_REPLY_NEW, dataclass=GroupTypes.WallReplyNew)
        async def new_wall_reply(event: GroupTypes.WallReplyNew):
            await comment_handle(event)

        @self.bot.on.raw_event(GroupEventType.LIKE_ADD, dataclass=GroupTypes.LikeAdd)
        async def like_add(event: GroupTypes.LikeAdd):
            await like_handle(event)

        for i in LABELERS:
            self.bot.labeler.load(i)
        self.bot.labeler.message_view.register_middleware(CommandMiddleware)

        rsl = Reboot.select().where(Reboot.sended == 0)
        for i in rsl:
            try:
                VK_API_SESSION.method('messages.send', {
                    'chat_id': i.chat_id,
                    'message': '💚 Перезагрузка выполнена!',
                    'random_id': 0
                })
            except:
                traceback.print_exc()
            i.sended = 1
            i.save()

        print('Started!')
        self.bot.run_forever()
