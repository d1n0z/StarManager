import asyncio
import sys
import traceback

from loguru import logger

from BotTG import Bot


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    logger.info("Starting...")
    try:
        asyncio.run(Bot().run())
    except KeyboardInterrupt:
        logger.info("bye-bye")
    except Exception:
        logger.critical(traceback.format_exc())
