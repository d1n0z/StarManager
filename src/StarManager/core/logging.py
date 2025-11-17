import logging
import sys
from loguru import Level, logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except Exception:
            level = Level.no
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def setup_logs():
    logger.remove()

    def filter_vk_api_error_spam(record):
        msg = record["message"]
        if "API error(s) in response wasn't handled" in msg:
            return False
        return True

    logger.add(sys.stderr, level="INFO", filter=filter_vk_api_error_spam)

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
