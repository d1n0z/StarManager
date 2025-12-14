import pytest
from tortoise import Tortoise

from StarManager.core.managers.custom_access_level import (
    CachedCustomAccessLevelRow,
    CustomAccessLevelManager,
    _make_cache_key,
)
from StarManager.core.tables import CustomAccessLevel


@pytest.fixture(scope="module")
async def init_db():
    # Инициализируем Tortoise с in-memory SQLite и моделями из приложения
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["StarManager.core.tables"]},
    )
    await Tortoise.generate_schemas()
    yield
    try:
        await Tortoise._drop_databases()
    except Exception:
        await Tortoise.close_connections()


@pytest.fixture()
async def manager(init_db):
    mgr = CustomAccessLevelManager()
    await mgr.initialize()
    yield mgr


@pytest.mark.asyncio
async def test_initialize_loads_db(init_db):
    await CustomAccessLevel.create(access_level=11, chat_id=1001, name="preload")
    mgr = CustomAccessLevelManager()
    await mgr.initialize()

    val = await mgr.get_access_level(11, 1001)  # type: ignore
    assert val == 11

    await mgr.delete(11, 1001)


@pytest.mark.asyncio
async def test_ensure_cached_returns_false_if_exists(manager):
    access_level, chat_id = 2, 2002
    # Создадим запись напрямую в БД
    await CustomAccessLevel.create(
        access_level=access_level, chat_id=chat_id, name="dbrow"
    )

    # Вызываем _ensure_cached — поскольку строки в БД есть, должно вернуться False
    created = await manager.cache._ensure_cached(_make_cache_key(access_level, chat_id))
    assert created is False

    # Теперь кеш обязан содержать запись
    assert await manager.get_access_level(access_level, chat_id) == access_level

    # Удалим
    await manager.delete(access_level, chat_id)


@pytest.mark.asyncio
async def test_edit_updates_fields_and_marks_dirty(manager):
    access_level, chat_id = 3, 3003
    key = _make_cache_key(access_level, chat_id)

    # Редактируем (создастся через _ensure_cached -> created True, добавится в кеш)
    await manager.edit(access_level, chat_id, name="Name1")

    # В кеше: поле name обновлено
    async with manager.cache._lock:
        obj = manager.cache._cache.get(key)
        assert obj is not None
        assert obj.name == "Name1"
        assert key in manager.cache._dirty

    # Sync должен записать в БД и очистить dirty
    await manager.cache.sync()
    async with manager.cache._lock:
        assert key not in manager.cache._dirty

    row = await CustomAccessLevel.filter(
        access_level=access_level, chat_id=chat_id
    ).first()
    assert row is not None and row.name == "Name1"

    # Cleanup
    await manager.delete(access_level, chat_id)


@pytest.mark.asyncio
async def test_edit_access_level_moves_key_when_exists_and_calls_repo_delete(
    monkeypatch, manager
):
    old_level, new_level, chat_id = 4, 40, 4004
    old_key = _make_cache_key(old_level, chat_id)
    new_key = _make_cache_key(new_level, chat_id)

    # Сначала создадим запись в кеше (через edit)
    await manager.edit(old_level, chat_id, name="oldname")
    async with manager.cache._lock:
        assert old_key in manager.cache._cache

    # Подменим repo.delete_record чтобы зафиксировать вызов
    called = {}

    async def fake_delete(a, b):
        called["args"] = (a, b)

    monkeypatch.setattr(manager.cache.repo, "delete_record", fake_delete)

    # Вызов edit_access_level для уже существующего ключа -> created == False -> перенос объекта
    await manager.edit_access_level(old_level, chat_id, new_level)

    async with manager.cache._lock:
        assert new_key in manager.cache._cache
        assert old_key not in manager.cache._cache
        assert new_key in manager.cache._dirty

    # repo.delete_record должен был вызваться с (old_level, chat_id)
    assert called.get("args") == (old_level, chat_id)

    # Cleanup
    await manager.delete(new_level, chat_id)


@pytest.mark.asyncio
async def test_edit_access_level_created_true_and_new_key_exists(manager):
    # Сценарий: cache не содержит старого ключа -> created True.
    # Но cache уже содержит новый ключ -> код должен обновить его access_level поле.
    old_level, new_level, chat_id = 5, 50, 5005
    old_key = _make_cache_key(old_level, chat_id)
    new_key = _make_cache_key(new_level, chat_id)

    # Подготовим в кеше заранее объект с new_key
    pre = CachedCustomAccessLevelRow(
        id=999, chat_id=chat_id, access_level=new_level, name="exists"
    )
    async with manager.cache._lock:
        manager.cache._cache[new_key] = pre

    # Убедимся, что старого ключа нет
    async with manager.cache._lock:
        assert old_key not in manager.cache._cache

    # Вызов edit_access_level: поскольку старого ключа нет, _ensure_cached создаст запись (created=True)
    # Чтобы repo.delete_record вызвался, проверим его поведение через непосредственное вызове менеджера
    await manager.edit_access_level(old_level, chat_id, new_level, "old_exists")

    # После выполнения new_key должен оставаться в кеше и его access_level должно быть new_level (оно и было)
    async with manager.cache._lock:
        assert new_key in manager.cache._cache
        assert manager.cache._cache[new_key].access_level == new_level
        assert new_key in manager.cache._dirty

    # Очистим
    await manager.delete(new_level, chat_id)


@pytest.mark.asyncio
async def test_remove_returns_deepcopy_and_deletes_repo(monkeypatch, manager):
    access_level, chat_id = 6, 6006
    key = _make_cache_key(access_level, chat_id)

    # Создаём запись в кеше
    await manager.edit(access_level, chat_id, name="to_remove")

    # Подменим repo.delete_record чтобы зафиксировать вызов
    called = {}

    async def fake_delete(a, b):
        called["args"] = (a, b)

    monkeypatch.setattr(manager.cache.repo, "delete_record", fake_delete)

    # Удаляем через manager.delete (делегирует cache.remove)
    removed = await manager.delete(access_level, chat_id)
    assert removed is not None
    assert removed.name == "to_remove"

    # Кеш не должен содержать ключ
    async with manager.cache._lock:
        assert key not in manager.cache._cache

    assert called.get("args") == (access_level, chat_id)


@pytest.mark.asyncio
async def test_sync_creates_and_updates_and_clears_dirty(manager):
    # Подготовим: одна запись в БД (чтобы обновить), одна — новая (чтобы создать)
    existing_level, chat_id = 7, 7007
    await CustomAccessLevel.create(
        access_level=existing_level, chat_id=chat_id, name="old_db_name"
    )
    # В кеше создадим "existing" ключ с другим именем -> должен обновиться
    await manager.edit(existing_level, chat_id, name="new_db_name")
    # И добавим новую запись в кеше, которой нет в БД
    new_level = 8
    await manager.edit(new_level, chat_id, name="created_name")

    # Убедимся, что оба ключа помечены dirty
    async with manager.cache._lock:
        assert _make_cache_key(existing_level, chat_id) in manager.cache._dirty
        assert _make_cache_key(new_level, chat_id) in manager.cache._dirty

    # Выполняем sync
    await manager.cache.sync()

    # После успешного sync dirty для этих ключей должен быть очищен
    async with manager.cache._lock:
        assert _make_cache_key(existing_level, chat_id) not in manager.cache._dirty
        assert _make_cache_key(new_level, chat_id) not in manager.cache._dirty

    # Проверим в БД
    row_existing = await CustomAccessLevel.filter(
        access_level=existing_level, chat_id=chat_id
    ).first()
    row_new = await CustomAccessLevel.filter(
        access_level=new_level, chat_id=chat_id
    ).first()
    assert row_existing is not None and row_existing.name == "new_db_name"
    assert row_new is not None and row_new.name == "created_name"

    # Cleanup
    await manager.delete(existing_level, chat_id)
    await manager.delete(new_level, chat_id)


@pytest.mark.asyncio
async def test_sync_exception_does_not_clear_dirty(monkeypatch, manager):
    level, chat_id = 9, 9009
    key = _make_cache_key(level, chat_id)

    # Создаём запись напрямую в кеш
    async with manager.cache._lock:
        manager.cache._cache[key] = CachedCustomAccessLevelRow(
            id=1, chat_id=chat_id, access_level=level, name="will_fail"
        )
        manager.cache._dirty.add(key)

    # Проверка: ключ точно в dirty
    async with manager.cache._lock:
        assert key in manager.cache._dirty

    # Патчим bulk_create чтобы вызвать исключение
    async def raising_bulk_create(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(CustomAccessLevel, "bulk_create", raising_bulk_create)

    # Запускаем sync — должно поймать исключение
    await manager.cache.sync()

    # После исключения ключ должен остаться в dirty
    async with manager.cache._lock:
        assert key in manager.cache._dirty

    # Очистка
    async with manager.cache._lock:
        manager.cache._cache.pop(key, None)
        manager.cache._dirty.discard(key)
