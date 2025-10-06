# tests/test_publicchats_manager.py
import asyncio
import time
import pytest
from tortoise import Tortoise

from StarManager.core.tables import PublicChats, UpCommandLogs
from StarManager.core.managers.public_chats import PublicChatsManager  # adjust path if needed


@pytest.fixture(scope="function")
async def init_db():
    """
    Initialize fresh in-memory SQLite DB per test and ensure it is fully dropped after the test.
    """
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["StarManager.core.tables"]},
    )
    await Tortoise.generate_schemas()

    # defensive: ensure tables are empty (in case of weird reuse)
    await PublicChats.all().delete()
    await UpCommandLogs.all().delete()

    yield

    # teardown: close connections and drop DBs to avoid cross-test pollution
    await Tortoise.close_connections()
    await Tortoise._drop_databases()


@pytest.fixture()
async def manager(init_db):
    mgr = PublicChatsManager()
    await mgr.initialize()
    yield mgr


@pytest.mark.asyncio
async def test_create_premium_and_up_and_sync(manager):
    chat_id = 1001
    uid = 500

    # ensure chat exists and set premium true
    await manager.ensure_chat(chat_id, defaults={"premium": False, "last_up": 0, "isopen": True})
    await manager.edit_chat(chat_id, premium=True)

    # initially, user can up
    can, rem = await manager.can_user_up(chat_id, uid)
    assert can is True
    assert rem == 0

    # perform /up
    success, remaining = await manager.do_up(chat_id, uid)
    assert success is True
    assert remaining is None

    # cache should be updated: last_up present and uplog present
    chat_obj = await manager.get_chat(chat_id)
    assert chat_obj is not None
    assert chat_obj.premium is True
    assert chat_obj.last_up > 0

    uplog = await manager.cache.get_uplog(chat_id, uid)
    assert uplog is not None
    assert uplog.timestamp == chat_obj.last_up

    # persist to DB
    await manager.sync()

    # new manager should load persisted values
    mgr2 = PublicChatsManager()
    await mgr2.initialize()
    loaded_chat = await mgr2.get_chat(chat_id)
    assert loaded_chat is not None
    assert loaded_chat.premium is True
    assert int(loaded_chat.last_up) == int(chat_obj.last_up)

    # uplog exists in DB
    row = await UpCommandLogs.filter(chat_id=chat_id, uid=uid).first()
    assert row is not None
    assert int(row.timestamp) == int(chat_obj.last_up)


@pytest.mark.asyncio
async def test_up_cooldown_per_user(manager):
    chat_id = 2002
    uid = 600

    await manager.ensure_chat(chat_id)
    await manager.edit_chat(chat_id, premium=True)

    # first up allowed
    can, rem = await manager.can_user_up(chat_id, uid)
    assert can is True
    assert rem == 0

    ok, _ = await manager.do_up(chat_id, uid)
    assert ok is True

    # second up immediately should be denied
    ok2, remaining = await manager.do_up(chat_id, uid)
    assert ok2 is False
    assert remaining is not None
    assert 0 < remaining <= 86400

    # simulate time by using now_ts param: after 24h allowed
    now_ts = int(time.time()) + 86400 + 1
    can_after, _ = await manager.can_user_up(chat_id, uid, now_ts=now_ts)
    assert can_after is True


@pytest.mark.asyncio
async def test_non_premium_cannot_up(manager):
    chat_id = 3003
    uid = 700

    await manager.ensure_chat(chat_id)
    await manager.edit_chat(chat_id, premium=False)

    ok, rem = await manager.do_up(chat_id, uid)
    assert ok is False
    assert rem is None  # manager returns (False, None) for non-premium per implementation


@pytest.mark.asyncio
async def test_concurrent_ups_multiple_users(manager):
    chat_id = 4004
    await manager.ensure_chat(chat_id)
    await manager.edit_chat(chat_id, premium=True)

    users = list(range(1000, 1010))

    async def worker(uid):
        await asyncio.sleep(0)
        res, rem = await manager.do_up(chat_id, uid)
        return uid, res, rem

    tasks = [asyncio.create_task(worker(u)) for u in users]
    results = await asyncio.gather(*tasks)

    allowed = [r for r in results if r[1] is True]
    assert len(allowed) == len(users)

    chat_obj = await manager.get_chat(chat_id)
    assert chat_obj.last_up > 0

    for u in users:
        upl = await manager.cache.get_uplog(chat_id, u)
        assert upl is not None

    await manager.sync()
    db_logs = await UpCommandLogs.filter(chat_id=chat_id).all()
    db_uids = {r.uid for r in db_logs}
    assert set(users).issubset(db_uids)


@pytest.mark.asyncio
async def test_sync_does_not_lose_updates(monkeypatch, manager):
    chat_id = 5005
    uid = 800
    await manager.ensure_chat(chat_id)
    await manager.edit_chat(chat_id, premium=True)

    await manager.do_up(chat_id, uid)

    orig_bulk_update_chats = PublicChats.bulk_update
    orig_bulk_create_chats = PublicChats.bulk_create
    orig_bulk_update_logs = UpCommandLogs.bulk_update
    orig_bulk_create_logs = UpCommandLogs.bulk_create

    async def delayed_bulk_update(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await orig_bulk_update_chats(*args, **kwargs)

    async def delayed_bulk_create(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await orig_bulk_create_chats(*args, **kwargs)

    async def delayed_logs_update(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await orig_bulk_update_logs(*args, **kwargs)

    async def delayed_logs_create(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await orig_bulk_create_logs(*args, **kwargs)

    monkeypatch.setattr(PublicChats, "bulk_update", delayed_bulk_update)
    monkeypatch.setattr(PublicChats, "bulk_create", delayed_bulk_create)
    monkeypatch.setattr(UpCommandLogs, "bulk_update", delayed_logs_update)
    monkeypatch.setattr(UpCommandLogs, "bulk_create", delayed_logs_create)

    await manager.edit_chat(chat_id, isopen=True)
    sync_task = asyncio.create_task(manager.sync())
    await asyncio.sleep(0.01)

    other_uid = 801
    await manager.do_up(chat_id, other_uid)

    await sync_task
    await manager.sync()

    mgr2 = PublicChatsManager()
    await mgr2.initialize()
    db_row = await UpCommandLogs.filter(chat_id=chat_id, uid=other_uid).first()
    assert db_row is not None
    assert db_row.timestamp > 0


@pytest.mark.asyncio
async def test_initialize_loads_existing_records(manager):
    chat_id = 6006
    uid = 900

    ts = int(time.time())
    await PublicChats.create(chat_id=chat_id, premium=True, last_up=ts, isopen=True)
    await UpCommandLogs.create(chat_id=chat_id, uid=uid, timestamp=ts)

    mgr2 = PublicChatsManager()
    await mgr2.initialize()

    loaded_chat = await mgr2.get_chat(chat_id)
    assert loaded_chat is not None
    assert loaded_chat.premium is True
    assert int(loaded_chat.last_up) == ts

    loaded_log = await mgr2.cache.get_uplog(chat_id, uid)
    assert loaded_log is not None
    assert int(loaded_log.timestamp) == ts


@pytest.mark.asyncio
async def test_remove_chat_and_sync(manager):
    chat_id = 7007
    uid = 1000

    await manager.ensure_chat(chat_id)
    await manager.edit_chat(chat_id, premium=True)
    await manager.do_up(chat_id, uid)
    await manager.sync()

    await manager.remove_chat(chat_id)
    assert await manager.get_chat(chat_id) is None

    await manager.sync()
    row = await PublicChats.filter(chat_id=chat_id).first()
    assert row is None
    logs = await UpCommandLogs.filter(chat_id=chat_id).all()
    assert logs == []
