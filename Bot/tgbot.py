import aiogram

from config.config import TG_TOKEN


def getTGBot():
    return aiogram.Bot(token=TG_TOKEN)
