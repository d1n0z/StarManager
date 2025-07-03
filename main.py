import os
import sys
import time
import traceback

from loguru import logger

from Bot import main as vkbot
from config.config import DAILY_TO, DATABASE, PATH, vk_api_session
from load_messages import load
from tables import Model, dbhandle


def run_bot(max_retries: int = 0, retry_delay: int = 30):
    attempt = 0
    
    while (attempt < max_retries) or not max_retries:
        try:
            vkbot.run()
        
        except KeyboardInterrupt:
            logger.info("Bot stopped by user (KeyboardInterrupt). Exiting...")
            return
        
        except Exception:
            logger.exception(f"Error in bot execution (attempt {attempt}{f'/{max_retries}' if max_retries else ''}):")
        attempt += 1
        
        if attempt == max_retries:
            logger.error("Max retries reached. Sending error notification and exiting...")
            send_error_notification()
            return
            
        logger.info(f"Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)


def send_error_notification() -> None:
    try:
        vk_api_session.method(
            "messages.send",
            {
                "chat_id": DAILY_TO,
                "message": f"Unexpected exception caught in VkBot.run():\n{traceback.format_exc()}",
                "random_id": 0,
            },
        )
    except Exception as notify_error:
        logger.error(f"Failed to send error notification: {notify_error}")
    logger.exception("Full traceback of the error:")


def main():
    def vkbottle_filter(record):
        message = record["message"]
        return "API error(s) in response wasn't handled" not in message

    logger.remove()
    logger.add(sys.stderr, level="INFO", filter=vkbottle_filter)

    logger.info("Starting...")
    os.system(f"rm {DATABASE}.sql {PATH + 'media/temp/*'} > /dev/null 2>&1")

    logger.info("Creating tables...")
    dbhandle.create_tables(Model.__subclasses__())

    logger.info("Loading messages...")
    load()

    logger.info("Starting scheduler...")
    os.system("tmux kill-session -t botscheduler")
    os.system(
        f"tmux new -s botscheduler -d && tmux send-keys -t botscheduler 'cd {PATH}' ENTER "
        f"'. {PATH + 'venv/bin/activate'}' ENTER 'python3.11 runscheduler.py' ENTER"
    )

    logger.info("Starting Telegram bot...")
    os.system("tmux kill-session -t bottg")
    os.system(
        f"tmux new -s bottg -d && tmux send-keys -t bottg 'cd {PATH}' ENTER "
        f"'. {PATH + 'venv/bin/activate'}' ENTER 'python3.11 runtg.py' ENTER"
    )

    logger.info("Loading...")
    run_bot()


if __name__ == "__main__":
    main()
