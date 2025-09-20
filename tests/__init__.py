import sys
import pytest


def main():
    pytest_args = ["-q", "--tb=short", "-vv", "./tests"]
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)
