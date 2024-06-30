from mega import Mega
from config.config import MEGA_LOGIN, MEGA_PASSWORD


def mega_drive():
    return Mega().login(MEGA_LOGIN, MEGA_PASSWORD)
