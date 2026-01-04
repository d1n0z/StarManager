import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def compress_and_remove(path: str, xz_path: Optional[str] = None, xz_level: str = "-9") -> None:
    if xz_path is None:
        xz_path = shutil.which("xz")

    if not xz_path:
        try:
            import lzma
            dst = path + ".xz"
            tmp = dst + ".tmp"
            with open(path, "rb") as src, lzma.open(tmp, "wb") as out:
                shutil.copyfileobj(src, out)
            os.replace(tmp, dst)
            os.remove(path)
            return
        except Exception as e:
            sys.stderr.write(f"[compress_with_xz] fallback lzma failed for {path}: {e}\n")
            raise

    dst = path + ".xz"
    tmp = dst + ".tmp"

    cmd = [xz_path, "-z", "-c", xz_level, path]

    try:
        with open(tmp, "wb") as out:
            subprocess.run(cmd, stdout=out, check=True)
        os.replace(tmp, dst)
        os.remove(path)
    except Exception as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        sys.stderr.write(f"[compress_with_xz] compression failed for {path}: {e}\n")
        raise


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except Exception:
            level = "INFO"
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def filter_vkbot_debug(record):
    if record["level"].name == "DEBUG" and record["name"].startswith("vkbottle"):
        return False
    return True


def setup_logs():
    logger.remove()

    # Глушим сторонний шум
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("yadisk").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("tortoise").setLevel(logging.WARNING)

    def filter_vk_api_error_spam(record):
        if "API error(s) in response wasn't handled" in record["message"]:
            return False
        return True

    logger.add(sys.stderr, level="INFO", filter=filter_vk_api_error_spam)

    logger.add(
        LOG_DIR / "debug.log",
        level="DEBUG",
        filter=filter_vkbot_debug,
        rotation="500 MB",
        compression=compress_and_remove,
        retention="7 days",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
