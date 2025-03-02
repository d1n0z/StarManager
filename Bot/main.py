from datetime import datetime

import pydantic
import vk_api.exceptions
import vkbottle.api.response_validator
from loguru import logger
from pydantic import v1
from vkbottle import GroupEventType, GroupTypes, VKAPIError
from vkbottle.framework.labeler import BotLabeler

from Bot.bot import bot
from Bot.labelers import LABELERS
from Bot.comment_handlers import comment_handle
from Bot.like_handlers import like_handle
from Bot.message_handlers import message_handle
from Bot.middlewares import CommandMiddleware
from Bot.reaction_handlers import reaction_handle
from config.config import vk_api_session
from db import syncpool, pool


def run():
    labeler = BotLabeler()
    # bot.loop_wrapper.add_task(scheduler.run())  # uses a lot of resources(somehow)

    @labeler.raw_event(GroupEventType.MESSAGE_REACTION_EVENT, dataclass=GroupTypes.MessageReactionEvent)
    async def reaction(event: GroupTypes.MessageReactionEvent):
        await reaction_handle(event)

    @labeler.raw_event(GroupEventType.MESSAGE_NEW, dataclass=GroupTypes.MessageNew, blocking=False)
    async def new_message(event: GroupTypes.MessageNew):
        timestart = datetime.now()
        await message_handle(event)
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute(
                    'insert into messagesstatistics (timestart, timeend) values (%s, %s)',
                    (timestart, datetime.now()))
                await conn.commit()

    @labeler.raw_event(GroupEventType.WALL_REPLY_NEW, dataclass=GroupTypes.WallReplyNew)
    async def new_wall_reply(event: GroupTypes.WallReplyNew):
        await comment_handle(event)

    @labeler.raw_event(GroupEventType.LIKE_ADD, dataclass=GroupTypes.LikeAdd)
    async def like_add(event: GroupTypes.LikeAdd):
        await like_handle(event)

    @bot.error_handler.register_error_handler(VKAPIError[7])
    @bot.error_handler.register_error_handler(VKAPIError[917])
    @bot.error_handler.register_error_handler(VKAPIError[100])
    @bot.error_handler.register_error_handler(VKAPIError[6])
    @bot.error_handler.register_error_handler(pydantic.ValidationError)
    @bot.error_handler.register_error_handler(v1.ValidationError)
    @bot.error_handler.register_error_handler(v1.error_wrappers.ValidationError)
    @bot.error_handler.register_error_handler(vkbottle.api.response_validator.VKAPIErrorResponseValidator)
    @bot.error_handler.register_error_handler(vk_api.exceptions.ApiError)
    async def exception_handler(e: Exception):  # noqa
        pass

    bot.labeler.load(labeler)
    for i in LABELERS:
        bot.labeler.load(i)
    bot.labeler.message_view.register_middleware(CommandMiddleware)

    with syncpool().connection() as conn:
        with conn.cursor() as c:
            rsl = c.execute('select id, chat_id from reboots where sended=false').fetchall()
            for i in rsl:
                try:
                    vk_api_session.method('messages.send', {
                        'chat_id': i[1],
                        'message': '💚 Перезагрузка выполнена!',
                        'random_id': 0
                    })
                except:
                    pass
                c.execute('update reboots set sended=true where id=%s', (i[0],))
            conn.commit()

    logger.info('Loaded. Starting the bot...')
    bot.run_forever()
