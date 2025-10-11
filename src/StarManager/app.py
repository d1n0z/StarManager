import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
import threading
import traceback

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
def install_sigint_debug(loop):
    async def _dump_and_cancel():
        logger.warning("SIGINT received: dumping tasks and threads...")

        # asyncio tasks
        tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
        logger.warning(f"Pending asyncio tasks: {len(tasks)}")
        for t in tasks:
            try:
                logger.warning(f"Task: {t.get_name()} repr={t!r}")
                for frm in t.get_stack(limit=10):
                    logger.warning("".join(traceback.format_list(traceback.extract_stack(frm))))
            except Exception:
                logger.exception("Error while dumping task stack")

        # threads
        thr = threading.enumerate()
        logger.warning(f"Threads: {len(thr)}")
        for th in thr:
            logger.warning(f"Thread: name={th.name} daemon={th.daemon} ident={th.ident}")

        # Cancel tasks (except current)
        me = asyncio.current_task(loop=loop)
        for t in tasks:
            if t is not me:
                t.cancel()

        # wait short time for tasks to finish
        try:
            await asyncio.wait_for(asyncio.gather(*[t for t in tasks if t is not me], return_exceptions=True), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Tasks did not finish within timeout after cancel")

    def _handler():
        # schedule the coroutine on the loop
        try:
            loop.create_task(_dump_and_cancel())
        except RuntimeError:
            # loop already stopped
            print("Loop already stopped", file=sys.stderr)

    # register for SIGINT and SIGTERM (if supported)
    try:
        loop.add_signal_handler(signal.SIGINT, _handler)
        loop.add_signal_handler(signal.SIGTERM, _handler)
    except NotImplementedError:
        # Windows: loop.add_signal_handler not implemented for some event loops
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    install_sigint_debug(asyncio.get_event_loop())
    logger.info("Lifespan startup: init DB and objects")
    await tables.init()
    await managers.initialize()

    app.state.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_jobs(app.state.scheduler)
    app.state.scheduler.start()
    logger.info("Scheduler started")

    app.state.bg_tasks = []

    await load_messages.load()

    vk_task = asyncio.create_task(vkbot_module.main().run_polling(), name="vkbot")
    app.state.bg_tasks.append((vk_task, None))

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
