import aiogram
from loguru import logger

from StarManager.tgbot import bot, handlers, middlewares


class Bot:
    def __init__(self):
        self.bot = bot.bot
        self.dp = aiogram.Dispatcher()

    async def setup(self, webhook_url: str):
        self.dp.include_router(handlers.router)
        self.dp.update.middleware.register(middlewares.ContextMsgDeleteMiddleware())
        if webhook_url:
            logger.info(f"Setting TG webhook to: {webhook_url}")
            await self.bot.set_webhook(webhook_url)
            info = await self.bot.get_webhook_info()
            logger.info(f"Webhook set: {info.url}")
        else:
            logger.info("No webhook URL, deleting webhook")
            await self.bot.delete_webhook(drop_pending_updates=True)

    async def close(self):
        await self.bot.session.close()
