import logging
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from routes import router
sys.path.append('../')
from config import config

logger = logging.getLogger(__name__)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(SessionMiddleware, secret_key=config.VK_APP_SECRET)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)
