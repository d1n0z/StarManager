import aiogram
from aiogram.client.default import DefaultBotProperties

from config import config

bot = aiogram.Bot(
    token=config.TG_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML", link_preview_is_disabled=True),
)
