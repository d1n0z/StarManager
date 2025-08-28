import asyncio
import sys

from loguru import logger

from StarManager import scheduler


def main():
    def vkbottle_filter(record):
        return "API error(s) in response wasn't handled" not in record["message"]

    logger.remove()
    logger.add(
        sys.stderr, level="INFO", filter=vkbottle_filter, backtrace=True, diagnose=True
    )
    loop = asyncio.new_event_loop()
    scheduler.run(loop)
    loop.run_forever()


if __name__ == "__main__":
    main()
