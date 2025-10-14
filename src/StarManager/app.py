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
        try:
            while True:
                await asyncio.sleep(60)
                from StarManager.core.db import pool as get_pool
                from StarManager.site.routes import _dropped_events, _vk_tasks

                try:
                    db_pool = await get_pool()
                    pool_info = f"DB: {db_pool.get_size() - db_pool.get_idle_size()}/{db_pool.get_size()}"
                except Exception:
                    pool_info = "DB: ?"
                logger.info(
                    f"VK tasks: {len(_vk_tasks)} | Dropped: {_dropped_events} | {pool_info}"
                )
        except asyncio.CancelledError:
            logger.info("Monitor task cancelled")
            raise

    monitor_task = asyncio.create_task(_monitor_tasks(), name="monitor")
    app.state.bg_tasks.append((monitor_task, None))

    logger.info("Lifespan startup complete, entering yield")
    try:
        yield
    finally:
        logger.info("Lifespan shutdown: stopping bg tasks and scheduler")
        tasks = asyncio.all_tasks()
        logger.warning(f"Active tasks at shutdown start: {len(tasks)}")
        for task in list(tasks)[:10]:
            logger.warning(f"  - {task.get_name()}")

        app.state.scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

        logger.info("Syncing managers...")
        try:
            await asyncio.wait_for(managers.close(), timeout=5)
            logger.info("Managers synced and closed")
        except asyncio.TimeoutError:
            logger.warning("Managers sync timeout, forcing close")
        except Exception as e:
            logger.error(f"Managers close error: {e}")

        from StarManager.site.routes import _vk_tasks

        if _vk_tasks:
            logger.warning(f"Cancelling {len(_vk_tasks)} pending VK tasks")
            for task in list(_vk_tasks):
                task.cancel()

        for t, obj in list(app.state.bg_tasks):
            if not t.done():
                t.cancel()

        await asyncio.sleep(0.1)

        for t, obj in list(app.state.bg_tasks):
            if obj and hasattr(obj, "close"):
                try:
                    await asyncio.wait_for(obj.close(), timeout=2)
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Object close failed: {e}")

        for t, _ in list(app.state.bg_tasks):
            try:
                await asyncio.wait_for(t, timeout=3)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            except Exception as e:
                logger.warning(f"Task wait error: {e}")

        logger.info("Shutdown complete")
        tasks = asyncio.all_tasks()
        logger.warning(f"Active tasks at shutdown end: {len(tasks)}")


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
