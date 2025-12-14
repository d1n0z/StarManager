import asyncio
import sys
from pathlib import Path

import pytest
from tortoise import Tortoise

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from StarManager.core.tables import AccessLevel, ChatUserCMIDs

DATABASE_URL = "sqlite://:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Создаем отдельный event loop для async тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db():
    """Инициализация Tortoise ORM и чистка БД после теста."""
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["StarManager.core.tables"]},
    )
    await Tortoise.generate_schemas()
    yield
    # Очистка таблиц после каждого теста
    for model in [ChatUserCMIDs, AccessLevel]:
        await model.all().delete()
    await Tortoise.close_connections()
