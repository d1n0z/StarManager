import sys

import uvicorn
from loguru import logger

from StarManager.site import app


def main():
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")


if __name__ == "__main__":
    main()
