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
from StarManager.vkbot import load_messages
from StarManager.vkbot.main import main as load_vkbot

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

    load_vkbot()

    app.state.bg_tasks = []

    await load_messages.load()

    tg_bot = TgBot()
    tg_task = asyncio.create_task(tg_bot.run(), name="tgbot")
    app.state.bg_tasks.append((tg_task, tg_bot.bot))
    
    async def _monitor_tasks():
        while True:
            await asyncio.sleep(60)
            from StarManager.site.routes import _vk_tasks
            logger.info(f"Active VK tasks: {len(_vk_tasks)}")
    
    monitor_task = asyncio.create_task(_monitor_tasks(), name="monitor")
    app.state.bg_tasks.append((monitor_task, None))

    try:
        yield
    finally:
        logger.info("Lifespan shutdown: stopping bg tasks and scheduler")

        app.state.scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

        logger.info("Syncing managers...")
        try:
            await asyncio.wait_for(managers.close(), timeout=30)
            logger.info("Managers synced and closed")
        except asyncio.TimeoutError:
            logger.warning("Managers sync timeout, forcing close")

        from StarManager.site.routes import _vk_tasks
        logger.info(f"Cancelling {len(_vk_tasks)} pending VK tasks")
        for task in list(_vk_tasks):
            task.cancel()
        
        for t, obj in list(app.state.bg_tasks):
            if obj and hasattr(obj, "close"):
                try:
                    await asyncio.wait_for(obj.close(), timeout=5)
                except asyncio.TimeoutError:
                    logger.warning(f"Object close timeout: {obj}")
            if not t.done():
                t.cancel()
        
        for t, _ in list(app.state.bg_tasks):
            try:
                await asyncio.wait_for(t, timeout=10)
            except asyncio.TimeoutError:
                logger.warning(f"Task {t.get_name()} did not stop in time")
                t.cancel()
            except asyncio.CancelledError:
                pass
        
        logger.info("Shutdown complete")


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
