from loguru import logger
from vkbottle import GroupEventType, GroupTypes
from vkbottle.framework.labeler import BotLabeler

from Bot.bot import bot
from Bot.labelers import LABELERS
from Bot.comment_handlers import comment_handle
from Bot.like_handlers import like_handle
from Bot.message_handlers import message_handle
from Bot.middlewares import CommandMiddleware
from Bot.reaction_handlers import reaction_handle
from config.config import vk_api_session
from db import syncpool


def run():
    labeler = BotLabeler()

    @labeler.raw_event(GroupEventType.MESSAGE_REACTION_EVENT, dataclass=GroupTypes.MessageReactionEvent)
    async def reaction(event: GroupTypes.MessageReactionEvent):
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
