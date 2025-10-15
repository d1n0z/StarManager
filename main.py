import sys
from argparse import ArgumentParser
from pathlib import Path
from loguru import logger
import uvicorn

sys.path.insert(0, str(Path(__file__).parent / "src"))

argparser = ArgumentParser()
argparser.add_argument("-t", "--tests", action="store_true", help="Run tests and exit")
argparser.add_argument("-ur", "--uvicorn-reload", action="store_true", help="Run in autoreload mode (development purposes)")

def main():
    args = argparser.parse_args()

    if args.tests:
        from tests import main as run_tests
        return run_tests()

    logger.info("Starting unified StarManager app...")
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
