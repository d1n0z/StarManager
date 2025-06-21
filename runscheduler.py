import asyncio
import sys

from loguru import logger

from Bot import scheduler

if __name__ == "__main__":

    def vkbottle_filter(record):
        message = record["message"]
        return "API error(s) in response wasn't handled" not in message

    logger.remove()
    logger.add(sys.stderr, level="INFO", filter=vkbottle_filter)
    loop = asyncio.new_event_loop()
    loop.create_task(scheduler.run())
    loop.run_forever()
