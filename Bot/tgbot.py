import telebot

from config.config import TG_TOKEN


def getTGBot():
    return telebot.TeleBot(TG_TOKEN)
