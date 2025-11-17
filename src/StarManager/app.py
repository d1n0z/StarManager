import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from StarManager import scheduler
from StarManager.core import managers, tables
from StarManager.core.config import settings
from StarManager.core.logging import setup_logs
from StarManager.site.routes import router
from StarManager.tgbot.main import Bot as TgBot
from StarManager.vkbot import load_messages
from StarManager.vkbot.main import main as load_vkbot

setup_logs()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan startup: init DB and objects")
    await tables.init()
    await managers.initialize()

    app.state.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    def scheduler_error_listener(event):
        if hasattr(event, "exception") and event.exception:
            logger.error(f"Scheduler job error: {event.job_id} - {event.exception}")

    app.state.scheduler.add_listener(scheduler_error_listener, EVENT_JOB_ERROR)

    scheduler.add_jobs(app.state.scheduler)
    app.state.scheduler.start()
    logger.info("Scheduler started")

    load_vkbot()

    app.state.bg_tasks = []

    from StarManager.core.event_queue import event_queue

    await event_queue.load_from_disk()

    await load_messages.load()

    tg_bot = TgBot()
    await tg_bot.setup(settings.telegram.webhook_url)
    app.state.tg_bot = tg_bot

    async def _process_queued_events():
        from StarManager.core.event_queue import event_queue
        from StarManager.site.routes import _vk_tasks, process_vk_event

        try:
            while True:
                if len(_vk_tasks) < 150 and event_queue.qsize() > 0:
                    data = await event_queue.get()
                    await process_vk_event(data, data.get("type"))
                else:
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Queue processor cancelled")
            raise

    async def _monitor_tasks():
        try:
            while True:
                await asyncio.sleep(60)
                from StarManager.core.db import pool as get_pool
                from StarManager.core.event_queue import event_queue
                from StarManager.site.routes import _vk_tasks

                try:
                    db_pool = await get_pool()
                    pool_info = f"DB: {db_pool.get_size() - db_pool.get_idle_size()}/{db_pool.get_size()}"
                except Exception:
                    pool_info = "DB: ?"
                logger.debug(
                    f"VK tasks: {len(_vk_tasks)} | Queued: {event_queue.qsize()} | {pool_info}"
                )
        except asyncio.CancelledError:
            logger.info("Monitor task cancelled")
            raise

    queue_processor = asyncio.create_task(
        _process_queued_events(), name="queue_processor"
    )
    app.state.bg_tasks.append((queue_processor, None))

    monitor_task = asyncio.create_task(_monitor_tasks(), name="monitor")
    app.state.bg_tasks.append((monitor_task, None))

    from StarManager.core.event_loop_monitor import event_loop_monitor

    loop_monitor_task = asyncio.create_task(
        event_loop_monitor.monitor(), name="loop_monitor"
    )
    app.state.bg_tasks.append((loop_monitor_task, None))
    logger.info("Event loop monitor started")

    logger.info("Lifespan startup complete, entering yield")
    try:
        yield
    finally:
        logger.info("Lifespan shutdown: stopping bg tasks and scheduler")

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

        from StarManager.core.event_queue import event_queue
        from StarManager.site.routes import _vk_tasks

        logger.info("Saving pending events to disk...")
        await event_queue.save_to_disk()

        if _vk_tasks:
            logger.warning(f"Cancelling {len(_vk_tasks)} pending VK tasks")
            for task in list(_vk_tasks):
                task.cancel()

        for t, obj in list(app.state.bg_tasks):
            if not t.done():
                t.cancel()

        await asyncio.sleep(0.1)

        if hasattr(app.state, "tg_bot"):
            try:
                await asyncio.wait_for(app.state.tg_bot.close(), timeout=2)
            except Exception as e:
                logger.warning(f"TG bot close failed: {e}")

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
