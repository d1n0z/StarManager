from loguru import logger
from vkbottle import GroupEventType, GroupTypes
from vkbottle.framework.labeler import BotLabeler

from StarManager.core import managers
from StarManager.vkbot.bot import bot
from StarManager.vkbot.comment_handlers import comment_handle
from StarManager.vkbot.handlers import found_labelers
from StarManager.vkbot.like_handlers import like_handle
from StarManager.vkbot.message_handlers import message_handle
from StarManager.vkbot.middlewares import CommandMiddleware
from StarManager.vkbot.reaction_handlers import reaction_handle


def main():
    labeler = BotLabeler()

    @labeler.raw_event(
        GroupEventType.MESSAGE_REACTION_EVENT, dataclass=GroupTypes.MessageReactionEvent
    )
    async def reaction(event: GroupTypes.MessageReactionEvent):
        await reaction_handle(event)

    @labeler.raw_event(
        GroupEventType.MESSAGE_NEW, dataclass=GroupTypes.MessageNew, blocking=False
    )
    async def new_message(event: GroupTypes.MessageNew):
        if (message := event.object.message) and (message.peer_id - 2000000000 > 0):
            await managers.chat_user_cmids.append_cmid(
                message.from_id,
                message.peer_id - 2000000000,
                message.conversation_message_id,
            )
        await message_handle(event)

    @labeler.raw_event(GroupEventType.WALL_REPLY_NEW, dataclass=GroupTypes.WallReplyNew)
    async def new_wall_reply(event: GroupTypes.WallReplyNew):
        await comment_handle(event)

    @labeler.raw_event(GroupEventType.LIKE_ADD, dataclass=GroupTypes.LikeAdd)
    async def like_add(event: GroupTypes.LikeAdd):
        await like_handle(event)

    bot.labeler.load(labeler)
    for labeler in found_labelers:
        bot.labeler.load(labeler)
    bot.labeler.message_view.register_middleware(CommandMiddleware)

    logger.info("Loaded. Starting the bot...")
    return bot
