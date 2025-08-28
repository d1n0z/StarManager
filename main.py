import sys
from argparse import ArgumentParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


argparser = ArgumentParser()
argparser.add_argument("-o", "--only-vkbot", action="store_true")
argparser.add_argument("-nsc", "--no-scheduler", action="store_true")
argparser.add_argument("-sc", "--scheduler", action="store_true")
argparser.add_argument("-ntg", "--no-telegram", action="store_true")
argparser.add_argument("-tg", "--telegram", action="store_true")
argparser.add_argument("-nst", "--no-site", action="store_true")
argparser.add_argument("-st", "--site", action="store_true")


def main():
    args = argparser.parse_args()
    if args.scheduler:
        from StarManager.runscheduler import main as run_scheduler

        return run_scheduler()
    if args.telegram:
        from StarManager.runtg import main as run_tgbot

        return run_tgbot()
    if args.site:
        from StarManager.runsite import main as run_site

        return run_site()
    if (
        not args
        or not (args.scheduler or args.telegram or args.site)
        or args.only_vkbot
    ):
        from StarManager.main import main as run_vkbot

        return run_vkbot(args)


if __name__ == "__main__":
    main()
