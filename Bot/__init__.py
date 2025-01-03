import asyncio
import traceback

import pydantic
import vk_api.exceptions
import vkbottle.api.response_validator
from loguru import logger
from pydantic import v1
from vkbottle import Bot, GroupEventType, GroupTypes, VKAPIError, LoopWrapper
from vkbottle.framework.labeler import BotLabeler

from Bot import scheduler
from Bot.exception_handler import exception_handle
from Bot.labelers import LABELERS
from Bot.comment_handlers import comment_handle
from Bot.like_handlers import like_handle
from Bot.message_handlers import message_handle
from Bot.middlewares import CommandMiddleware
from Bot.reaction_handlers import reaction_handle
from config.config import VK_TOKEN_GROUP, VK_API_SESSION
from db import syncpool


class VkBot:
    def __init__(self):
        try:
            w = LoopWrapper()
            w.loop = asyncio.new_event_loop()
            self.bot = Bot(VK_TOKEN_GROUP, loop_wrapper=w)
        except Exception as e:
            print(e)

    def run(self):

        labeler = BotLabeler()

        # self.bot.loop_wrapper.add_task(scheduler.run())

        @labeler.raw_event(GroupEventType.MESSAGE_REACTION_EVENT, dataclass=GroupTypes.MessageReactionEvent)
        async def start(event: GroupTypes.MessageReactionEvent):
            await reaction_handle(event)

        @labeler.raw_event(GroupEventType.MESSAGE_NEW, dataclass=GroupTypes.MessageNew, blocking=False)
        async def new_message(event: GroupTypes.MessageNew):
            await message_handle(event)

        @labeler.raw_event(GroupEventType.WALL_REPLY_NEW, dataclass=GroupTypes.WallReplyNew)
        async def new_wall_reply(event: GroupTypes.WallReplyNew):
            await comment_handle(event)

        @labeler.raw_event(GroupEventType.LIKE_ADD, dataclass=GroupTypes.LikeAdd)
        async def like_add(event: GroupTypes.LikeAdd):
            await like_handle(event)

        # @self.bot.error_handler.register_error_handler(VKAPIError[917])
        # async def exception_handler(e: VKAPIError):
        #     pass  # await exception_handle(e)

        @self.bot.error_handler.register_error_handler(VKAPIError[7])
        @self.bot.error_handler.register_error_handler(VKAPIError[917])
        @self.bot.error_handler.register_error_handler(VKAPIError[100])
        @self.bot.error_handler.register_error_handler(pydantic.ValidationError)
        @self.bot.error_handler.register_error_handler(v1.ValidationError)
        @self.bot.error_handler.register_error_handler(v1.error_wrappers.ValidationError)
        @self.bot.error_handler.register_error_handler(vkbottle.api.response_validator.VKAPIErrorResponseValidator)
        @self.bot.error_handler.register_error_handler(vk_api.exceptions.ApiError)
        async def exception_handler(e: Exception):  # noqa
            pass

        self.bot.labeler.load(labeler)
        for i in LABELERS:
            self.bot.labeler.load(i)
        self.bot.labeler.message_view.register_middleware(CommandMiddleware)

        with syncpool().connection() as conn:
            with conn.cursor() as c:
                rsl = c.execute('select id, chat_id from reboots where sended=false').fetchall()
                for i in rsl:
                    try:
                        VK_API_SESSION.method('messages.send', {
                            'chat_id': i[1],
                            'message': '💚 Перезагрузка выполнена!',
                            'random_id': 0
                        })
                    except:
                        traceback.print_exc()
                    c.execute('update reboots set sended=true where id=%s', (i[0],))
                conn.commit()

        logger.info('Loaded. Starting the bot...')
        self.bot.run_forever()
