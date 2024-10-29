import asyncio
import sys

from loguru import logger

from Bot import scheduler


if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stderr, level='INFO')
    loop = asyncio.new_event_loop()
    loop.create_task(scheduler.run())
    loop.run_forever()
