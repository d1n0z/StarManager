import logging
import sys

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from routes import router
from starlette.middleware.sessions import SessionMiddleware

sys.path.append("../")
from config import config

logger = logging.getLogger(__name__)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
print(config.VK_APP_SECRET)
app.add_middleware(SessionMiddleware, secret_key=config.VK_APP_SECRET)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)


@app.exception_handler(404)
async def notfound(*_, **__):
    return RedirectResponse("/")
