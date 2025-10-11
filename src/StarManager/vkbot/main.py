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


def main(run=False):
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
    if run:
        bot.loop_wrapper.add_task(managers.initialize())
        bot.run_forever()
    else:
        return bot


async def run_bot():
    import random
    from asyncio import Task, create_task, sleep

    from loguru import logger
    from vkbottle import ABCPolling, VKAPIError
    from vkbottle.bot import Bot

    class PollingManager:
        MAX_EMPTY_UPDATES = 500

        def __init__(
            self, bot: Bot | None = None, max_retries: int = 5, base_delay: float = 0.5
        ):
            self.bot: Bot | None = bot
            self.polling: ABCPolling | None = bot.polling if bot else None
            self.max_retries = max_retries
            self.base_delay = base_delay
            self.retry_count = 0
            self.empty_update_count = 0
            self._health_check_task: Task | None = None

        def set_bot(self, bot: Bot):
            self.bot = bot
            self.polling = bot.polling

        async def start(self):
            if not self.bot or not self.polling:
                raise ValueError(
                    "Bot instance is not set. Use PollingManager.set_bot(vkbottle.bot.Bot()) before starting or pass corresponding parameter when creating the manager instance."
                )
            self._health_check_task = create_task(self._periodic_health_check())
            try:
                while True:
                    await self._ensure_session_active()

                    if self.polling is None:
                        break

                    async for event in self.polling.listen():
                        self.retry_count = 0

                        updates = event.get("updates")
                        if not updates:
                            self.empty_update_count += 1
                            if self.empty_update_count >= self.MAX_EMPTY_UPDATES:
                                logger.warning("Too many empty updates, reconnecting")
                                break
                            await sleep(self.base_delay)
                            continue

                        self.empty_update_count = 0
                        for update in updates:
                            try:
                                await self.bot.router.route(update, self.polling.api)
                            except Exception as e:
                                logger.error(f"Update processing error: {e}")

                    await sleep(self.base_delay)

            except VKAPIError as e:
                await self._handle_api_error(e)

            except TimeoutError:
                logger.warning("Polling timeout, reconnecting")
                await sleep(self.base_delay)
                await self._ensure_session_active()

            except Exception as e:
                await self._handle_generic_error(e)

            await self._shutdown()

        async def _handle_api_error(self, error: VKAPIError):
            if error.code == 29:  # rate limit
                self.retry_count += 1
                delay = min(2**self.retry_count + random.uniform(0, 1), 10)
                logger.warning(
                    f"Rate limit reached (attempt {self.retry_count}/{self.max_retries}), sleeping {delay}s"
                )
                await sleep(delay)
                if self.retry_count >= self.max_retries:
                    logger.error(
                        "Max retries reached due to rate limits, stopping polling"
                    )
            else:
                logger.error(f"VK API error: {error}")

        async def _handle_generic_error(self, error: Exception):
            self.retry_count += 1
            delay = min(2**self.retry_count + random.uniform(0, 1), 60)
            logger.warning(
                f"Polling error (attempt {self.retry_count}/{self.max_retries}): {error}"
            )
            await sleep(delay)
            if self.retry_count >= self.max_retries:
                logger.error("Max retries reached, stopping polling")
            await self._ensure_session_active()

        async def _periodic_health_check(self):
            while True:
                await sleep(60)
                await self._ensure_session_active()

        async def _ensure_session_active(self):
            try:
                if self.bot is None or not (
                    polling := getattr(self.bot, "polling", None)
                ):
                    await self._reinitialize_api()
                    return

                api = getattr(polling, "api", None)
                if not api:
                    logger.warning("Polling API is None. Skipping.")
                    return

                try:
                    if getattr(api, "closed", False) or (
                        callable(getattr(api, "is_closed", None)) and api.is_closed()
                    ):
                        logger.warning("Session closed, reinitializing")
                        await self._reinitialize_api()
                except Exception as e:
                    logger.error(f"Error checking if API is closed: {e}")
                    await self._reinitialize_api()

            except Exception as e:
                logger.error(f"Error checking session: {e}")
                await self._reinitialize_api()

        async def _reinitialize_api(self):
            try:
                if self.bot is None or self.polling is None:
                    logger.warning("Bot is not initialized. Skipping reinitialization.")
                    return

                if not self.polling or not hasattr(self.polling, "api"):
                    logger.warning("Polling or API not available, skipping reinit")
                    return

                api = self.polling.api

                if hasattr(api, "close"):
                    await api.close()  # type: ignore
                elif hasattr(api, "disconnect"):
                    await api.disconnect()  # type: ignore

                token = getattr(self.bot.api, "token", None)
                if not token and hasattr(self.bot.api, "token_generator"):
                    token = await self.bot.api.token_generator.get_token()

                if not token:
                    logger.error("Unable to retrieve token, API reinit failed")
                    return

                self.polling = self.polling.__class__()
                self.polling.api = self.bot.api
                logger.info("Polling reinitialized successfully")

            except Exception as e:
                logger.error(f"Failed to reinitialize API: {e}")

        async def _shutdown(self):
            if self._health_check_task:
                self._health_check_task.cancel()
            try:
                polling = getattr(self.bot, "polling", None)
                if not polling:
                    return

                api = getattr(polling, "api", None)
                if not api:
                    return

                if hasattr(api, "close") and not api.closed:
                    await api.close()
                elif hasattr(api, "disconnect") and not api.is_closed():
                    await api.disconnect()

            except Exception as e:
                logger.error(f"Error closing polling: {e}")

    logger.info("VKbot startup")
    await PollingManager(main()).start()
