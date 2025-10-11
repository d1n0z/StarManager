import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from StarManager import scheduler
from StarManager.core import managers, tables
from StarManager.core.config import settings
from StarManager.site.routes import router
from StarManager.tgbot.main import Bot as TgBot
from StarManager.vkbot.bot import bot as vkbot
from StarManager.vkbot import load_messages
from StarManager.vkbot import main as vkbot_module

logger.remove()
logger.add(sys.stderr, level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan startup: init DB and objects")
    await tables.init()
    await managers.initialize()

    app.state.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_jobs(app.state.scheduler)
    app.state.scheduler.start()
    logger.info("Scheduler started")

    app.state.bg_tasks = []

    await load_messages.load()

    tg_bot = TgBot()
    tg_task = asyncio.create_task(tg_bot.run(), name="tgbot")
    app.state.bg_tasks.append((tg_task, tg_bot.bot))

    try:
        yield
    finally:
        logger.info("Lifespan shutdown: stopping bg tasks and scheduler")
        app.state.scheduler.shutdown(wait=False)

        await managers.close()

        for t, obj in list(app.state.bg_tasks):
            if hasattr(obj, "close"):
                await obj.close()
            if not t.done():
                t.cancel()
        for t in list(app.state.bg_tasks):
            try:
                await asyncio.wait_for(t, timeout=5)
            except asyncio.TimeoutError:
                logger.warning(f"Task {t.get_name()} did not stop in time")
                t.cancel()


app = FastAPI(title="StarManager", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.vk.app_secret)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "site" / "static"),
    name="static",
)
app.include_router(router)


@app.exception_handler(404)
async def notfound(*_, **__):
    return RedirectResponse("/")
