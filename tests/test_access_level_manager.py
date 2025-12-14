    # pytest-asyncio tests for AccessLevel cache/manager
    # Adjust import paths if your project layout differs.
    # These tests assume:
    # - Tortoise model AccessLevel is available at StarManager.core.tables.AccessLevel
    # - The AccessLevelManager class (and related cache/repo) is defined in
    #   StarManager.core.managers.access_level
    # If your module path is different, change the imports below.

import asyncio
import pytest
from tortoise import Tortoise

from StarManager.core.tables import AccessLevel
from StarManager.core.managers.access_level import AccessLevelManager


@pytest.fixture(scope="module")
async def init_db():
    # Initialize Tortoise with in-memory SQLite for tests
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["StarManager.core.tables"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()


@pytest.fixture()
async def manager(init_db):
    mgr = AccessLevelManager()
    await mgr.initialize()
    yield mgr


@pytest.mark.asyncio
async def test_basic_crud_and_sync(manager):
    uid, chat_id = 123, 10

    # Initially absent
    assert await manager.get_access_level(uid, chat_id) == 0

    # Edit and persist
    await manager.edit_access_level(uid, chat_id, 5)
    # cache holds 5
    assert await manager.get_access_level(uid, chat_id) == 5

    # sync -> persists to DB
    await manager.sync()

    # create a fresh manager to ensure reading from DB
    mgr2 = AccessLevelManager()
    await mgr2.initialize()
    assert await mgr2.get_access_level(uid, chat_id) == 5

    # delete
    await manager.delete(uid, chat_id)
    assert await manager.get_access_level(uid, chat_id) == 0


@pytest.mark.asyncio
async def test_concurrent_edits_single_manager_no_loss(manager):
    uid, chat_id = 555, 42

    async def worker(start, step, count):
        for i in range(count):
            await manager.edit_access_level(uid, chat_id, start + i * step)
            # small sleep to increase concurrency
            await asyncio.sleep(0.001)

    # spawn multiple concurrent updaters for same (uid, chat_id)
    tasks = [asyncio.create_task(worker(100, 1, 50)) for _ in range(4)]
    await asyncio.gather(*tasks)

    # after concurrent edits, the cache should hold some int
    cached = await manager.get_access_level(uid, chat_id)
    assert isinstance(cached, int)

    # sync and ensure DB receives the last cached value
    await manager.sync()

    mgr2 = AccessLevelManager()
    await mgr2.initialize()
    dbv = await mgr2.get_access_level(uid, chat_id)
    assert dbv == cached


@pytest.mark.asyncio
async def test_no_overwrite_if_changed_during_sync(monkeypatch, manager):
    """
    Ensure that when a sync is in-flight and a value changes in cache,
    the newer value is not lost (i.e. will be persisted by a subsequent sync).

    We patch heavy DB operations to introduce a small delay, allowing us to
    update the cache while sync is mid-flight.
    """
    uid, chat_id = 777, 99

    # Prepare initial value and ensure it's in cache
    await manager.edit_access_level(uid, chat_id, 1)

    # Patch bulk_create/create/update to introduce a sleep so we have a window
    orig_bulk_create = AccessLevel.bulk_create
    orig_bulk_update = AccessLevel.bulk_update

    async def delayed_bulk_create(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await orig_bulk_create(*args, **kwargs)

    async def delayed_bulk_update(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await orig_bulk_update(*args, **kwargs)

    monkeypatch.setattr(AccessLevel, "bulk_create", delayed_bulk_create)
    monkeypatch.setattr(AccessLevel, "bulk_update", delayed_bulk_update)

    # Start sync in background (it will sleep inside bulk_*)
    sync_task = asyncio.create_task(manager.sync())

    # Give sync a moment to take its snapshot and reach the delayed DB call
    await asyncio.sleep(0.01)

    # Update the value while sync is in-flight
    await manager.edit_access_level(uid, chat_id, 2)

    # Wait for first sync to finish
    await sync_task

    # At this point the DB may contain the old value (1) or the new (2),
    # but the important guarantee is that the new value should eventually be
    # persisted. Do a second sync to flush the newer value.
    await manager.sync()

    # Read from DB using fresh manager instance
    mgr2 = AccessLevelManager()
    await mgr2.initialize()
    final = await mgr2.get_access_level(uid, chat_id)
    assert final == 2

    # restore originals (monkeypatch will handle this automatically on test teardown)
