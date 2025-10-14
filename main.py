# ./main.py
import asyncio
import signal
import sys
from argparse import ArgumentParser
from pathlib import Path
from loguru import logger
import uvicorn

sys.path.insert(0, str(Path(__file__).parent / "src"))

_shutdown_initiated = False

def _signal_handler(signum, frame):
    global _shutdown_initiated
    if _shutdown_initiated:
        logger.warning(f"Signal {signum} received again, forcing exit")
        import os
        os._exit(1)
    _shutdown_initiated = True
    logger.warning(f"Signal {signum} received in main.py")
    try:
        loop = asyncio.get_event_loop()
        tasks = asyncio.all_tasks(loop)
        logger.warning(f"Active tasks: {len(tasks)}")
        for task in tasks:
            coro = task.get_coro()
            logger.warning(f"  - {task.get_name()}: {coro.__qualname__ if hasattr(coro, '__qualname__') else coro}")
    except Exception as e:
        logger.warning(f"Could not list tasks: {e}")

argparser = ArgumentParser()
argparser.add_argument("-t", "--tests", action="store_true", help="Run tests and exit")
argparser.add_argument("-ur", "--uvicorn-reload", action="store_true", help="Run in autoreload mode (development purposes)")

def main():
    args = argparser.parse_args()

    if args.tests:
        from tests import main as run_tests
        return run_tests()

    logger.info("Starting unified StarManager app...")
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    import StarManager.app  # noqa: F401
    uvicorn.run(
        "StarManager.app:app",
        host="127.0.0.1",
        port=5000,
        reload=args.uvicorn_reload,
        log_level="info",
        access_log=False
    )
    return

if __name__ == "__main__":
    main()
