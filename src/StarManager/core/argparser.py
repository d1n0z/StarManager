from argparse import ArgumentParser


argparser = ArgumentParser()
argparser.add_argument("-p", "--port", type=int, default=5000, help="Port to run on")
argparser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run on")
argparser.add_argument("-t", "--tests", action="store_true", help="Run tests and exit")
argparser.add_argument(
    "-ur",
    "--uvicorn-reload",
    action="store_true",
    help="Run in autoreload mode (development purposes)",
)
