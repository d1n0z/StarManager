import logging
import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except Exception:
            level = "INFO"
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def setup_logs():
    logger.remove()

    # Глушим сторонний шум
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("yadisk").setLevel(logging.WARNING)

    def filter_vk_api_error_spam(record):
        if "API error(s) in response wasn't handled" in record["message"]:
            return False
        return True

    logger.add(sys.stderr, level="INFO", filter=filter_vk_api_error_spam)

    logger.add(
        LOG_DIR / "debug.log",
        level="DEBUG",
        rotation="500 MB",
        compression="xz",
        retention="7 days",
        backtrace=True,
        diagnose=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
