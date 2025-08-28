import aiogram
from aiogram.client.default import DefaultBotProperties

from StarManager.core.config import settings

bot = aiogram.Bot(
    token=settings.telegram.token,
    default=DefaultBotProperties(parse_mode="HTML", link_preview_is_disabled=True),
)
