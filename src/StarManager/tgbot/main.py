import aiogram

from StarManager.tgbot import bot, handlers, middlewares


class Bot:
    def __init__(self):
        self.bot = bot.bot
        self.dp = aiogram.Dispatcher()

    async def run(self):
        self.dp.include_router(handlers.router)
        self.dp.update.middleware.register(middlewares.ContextMsgDeleteMiddleware())
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)
        await self.bot.session.close()
