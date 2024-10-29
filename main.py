import asyncio
import sys
import traceback

from loguru import logger

from Bot import VkBot
from config.config import DATABASE, PATH
import os

from db import pool
from tables import dbhandle, Model
from load_messages import load

if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stderr, level='INFO')

    logger.info('Starting...')
    os.system(f'rm {DATABASE}.sql {PATH + "media/temp/*"}')

    logger.info('Creating tables...')
    dbhandle.create_tables(Model.__subclasses__())

    logger.info('Loading messages...')
    load()

    logger.info('Starting scheduler...')
    os.system("tmux kill-session -t botscheduler")
    os.system(f"tmux new -s botscheduler -d && tmux send-keys -t botscheduler 'cd {PATH}' ENTER "
              f"'. {PATH + 'venv/bin/activate'}' ENTER 'python3.11 runscheduler.py' ENTER")

    logger.info('Starting the bot...')
    try:
        try:
            VkBot().run()
        except:
            os.system("tmux kill-session -t botscheduler")
            raise
    except KeyboardInterrupt:
        logger.info('bye-bye')
    except Exception as e:
        logger.exception(traceback.format_exc())
