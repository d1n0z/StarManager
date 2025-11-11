import sys
from pathlib import Path

import uvicorn
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    from StarManager.core.argparser import argparser

    args = argparser.parse_args()

    if args.tests:
        from tests import main as run_tests

        return run_tests()

    logger.info("Starting unified StarManager app...")
    import StarManager.app  # noqa: F401

    uvicorn.run(
        "StarManager.app:app",
        host=args.host,
        port=args.port,
        reload=args.uvicorn_reload,
        log_level="info",
        access_log=False,
    )
    return


if __name__ == "__main__":
    main()
