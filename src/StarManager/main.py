import subprocess
import sys
import time
from argparse import Namespace

from loguru import logger

from StarManager.core import tables
from StarManager.core.config import settings
from StarManager.vkbot import load_messages
from StarManager.vkbot import main as vkbot
from StarManager.vkbot.bot import bot


def run_service(session: str, cmd: str | None = None, skip: bool = False):
    if skip or cmd is None:
        logger.info(f"Skipping {session}.")
        return

    logger.info(f"Starting {session}...")
    try:
        subprocess.run(["tmux", "kill-session", "-t", session], check=False)
        subprocess.run(
            [
                "tmux",
                "new",
                "-s",
                session,
                "-d",
                f"cd {settings.service.path} && . {settings.service.path}/venv/bin/activate && {cmd}",
            ],
            check=True,
        )
    except Exception:
        logger.exception(f"Failed to start {session}:")


def run_bot(max_retries: int = 0, retry_delay: int = 30):
    attempt = 0

    while (attempt < max_retries) or not max_retries:
        try:
            vkbot.run()

        except KeyboardInterrupt:
            logger.info("Bot stopped by user (KeyboardInterrupt). Exiting...")
            return

        except Exception:
            logger.exception(
                f"Error in bot execution (attempt {attempt}{f'/{max_retries}' if max_retries else ''}):"
            )
        attempt += 1

        if attempt == max_retries:
            logger.error(
                "Max retries reached. Sending error notification and exiting..."
            )
            send_error_notification()
            return

        logger.warning(f"Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)


def send_error_notification() -> None:
    # try:
    #     vk_api_session.method(
    #         "messages.send",
    #         {
    #             "chat_id": DAILY_TO,
    #             "message": f"Unexpected exception caught in VkBot.run():\n{traceback.format_exc()}",
    #             "random_id": 0,
    #         },
    #     )
    # except Exception as notify_error:
    #     logger.error(f"Failed to send error notification: {notify_error}")
    logger.exception("Full traceback of the error:")


def main(args: Namespace | None):
    def vkbottle_filter(record):
        message = record["message"]
        return "API error(s) in response wasn't handled" not in message

    logger.remove()
    logger.add(sys.stderr, level="INFO", filter=vkbottle_filter)

    logger.info("Starting...")
    subprocess.run(
        [
            "rm",
            f"{settings.database.name}.sql",
            settings.service.path + "media/temp/*",
            settings.service.path + "media/tmp/*",
            ">",
            "/dev/null",
            "2>&1",
        ], shell=True, check=False
    )

    logger.info("Creating tables...")
    bot.loop_wrapper.add_task(tables.init())

    logger.info("Loading messages...")
    bot.loop_wrapper.add_task(load_messages.load())

    run_service(
        "scheduler",
        "python3.11 main.py -sc",
        bool(args and args.no_scheduler and not args.only_vkbot),
    )

    run_service(
        "tgbot",
        "python3.11 main.py -tg",
        bool(args and args.no_telegram and not args.only_vkbot),
    )

    run_service(
        "site",
        "python3.11 main.py -st",
        bool(args and args.no_site and not args.only_vkbot),
    )

    logger.info("Loading...")
    run_bot()


if __name__ == "__main__":
    main(None)
