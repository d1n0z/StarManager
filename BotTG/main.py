
import asyncio

import aiogram

from BotTG import bot, handlers, middlewares, scheduler


class Bot:
    def __init__(self):
        self.bot = bot.bot
        self.dp = aiogram.Dispatcher()

    async def run(self):
        self.dp.include_router(handlers.router)
        self.dp.update.middleware.register(middlewares.ContextMsgDeleteMiddleware())
        await scheduler.run(asyncio.get_event_loop())
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)
