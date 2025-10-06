from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from StarManager.core import managers
from StarManager.core.config import settings
from StarManager.site.routes import router

logger.remove()
logger.add(sys.stderr, level="INFO")
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SessionMiddleware, secret_key=settings.vk.app_secret)
app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)
app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await managers.public_chats.initialize()
    yield


@app.exception_handler(404)
async def notfound(*_, **__):
    return RedirectResponse("/")
