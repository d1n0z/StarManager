import sys
import time
import traceback

from loguru import logger
from whois.whois import logger as whoislogger

from Bot import VkBot
from config.config import DATABASE, PATH, VK_API_SESSION, DAILY_TO
import os

from tables import dbhandle, Model
from load_messages import load


def main(retry=0, vkbot=VkBot()):
    whoislogger.disabled = True
    logger.remove()
    logger.add(sys.stderr, level='INFO')

    logger.info('Starting...')
    os.system(f'rm {DATABASE}.sql {PATH + "media/temp/*"} > /dev/null 2>&1')

    logger.info('Creating tables...')
    dbhandle.create_tables(Model.__subclasses__())

    logger.info('Loading messages...')
    load()

    logger.info('Starting scheduler...')
    os.system("tmux kill-session -t botscheduler")
    os.system(f"tmux new -s botscheduler -d && tmux send-keys -t botscheduler 'cd {PATH}' ENTER "
              f"'. {PATH + 'venv/bin/activate'}' ENTER 'python3.11 runscheduler.py' ENTER")

    logger.info('Starting Telegram bot...')
    os.system("tmux kill-session -t bottg")
    os.system(f"tmux new -s bottg -d && tmux send-keys -t bottg 'cd {PATH}' ENTER "
              f"'. {PATH + 'venv/bin/activate'}' ENTER 'python3.11 runtg.py' ENTER")

    logger.info('Loading...')
    try:
        try:
            vkbot.run()
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(e)
            os.system("tmux kill-session -t botscheduler")
        logger.info('ERROR! Retarting the bot in 15 seconds...')
        time.sleep(15)
        main(retry + 1, vkbot)
    except KeyboardInterrupt:
        logger.info('bye-bye')
        return
    except:
        VK_API_SESSION.method('messages.send', {
            'chat_id': DAILY_TO,
            'message': f'Unexpected exception caught in VkBot.run():\n{traceback.format_exc()}',
            'random_id': 0
        })
        logger.exception(traceback.format_exc())
        return


if __name__ == '__main__':
    main()
