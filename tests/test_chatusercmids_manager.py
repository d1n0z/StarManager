import pytest
import asyncio

from StarManager.core.managers.chatusercmids import ChatUserCMIDsManager
from StarManager.core.tables import ChatUserCMIDs


@pytest.mark.asyncio
async def test_basic_append_and_get(monkeypatch, db):
    manager = ChatUserCMIDsManager()
    await manager.initialize()

    uid, chat_id = 1, 100
    cmids = [10, 20, 30]

    # append cmids
    for cmid in cmids:
        await manager.append_cmid(uid, chat_id, cmid)

    # check get_cmids
    result = await manager.get_cmids(uid, chat_id)
    assert set(result) == set(cmids)

    # sync to DB
    await manager.sync()

    # check DB records
    db_cmids = await ChatUserCMIDs.filter(uid=uid, chat_id=chat_id)
    db_set = {row.cmid for row in db_cmids}
    assert db_set == set(cmids)


@pytest.mark.asyncio
async def test_no_duplicate_on_append(monkeypatch, db):
    manager = ChatUserCMIDsManager()
    await manager.initialize()

    uid, chat_id = 2, 200
    cmid = 42

    # append the same cmid multiple times
    for _ in range(3):
        await manager.append_cmid(uid, chat_id, cmid)

    result = await manager.get_cmids(uid, chat_id)
    assert result == (cmid,)

    await manager.sync()
    db_cmids = await ChatUserCMIDs.filter(uid=uid, chat_id=chat_id)
    assert len(db_cmids) == 1
    assert db_cmids[0].cmid == cmid


@pytest.mark.asyncio
async def test_sync_multiple_users(db):
    manager = ChatUserCMIDsManager()
    await manager.initialize()

    data = {
        (1, 100): [1, 2, 3],
        (2, 100): [4, 5],
        (1, 101): [6],
    }

    # append cmids
    for key, cmids in data.items():
        uid, chat_id = key
        for cmid in cmids:
            await manager.append_cmid(uid, chat_id, cmid)

    await manager.sync()

    # check DB
    for key, cmids in data.items():
        uid, chat_id = key
        rows = await ChatUserCMIDs.filter(uid=uid, chat_id=chat_id)
        assert set(row.cmid for row in rows) == set(cmids)


@pytest.mark.asyncio
async def test_concurrent_append_same_key(db):
    manager = ChatUserCMIDsManager()
    await manager.initialize()

    uid, chat_id = 3, 300
    cmids = list(range(10))

    async def append_all():
        for cmid in cmids:
            await manager.append_cmid(uid, chat_id, cmid)

    # run multiple appenders concurrently
    await asyncio.gather(append_all(), append_all(), append_all())

    result = await manager.get_cmids(uid, chat_id)
    assert set(result) == set(cmids)

    await manager.sync()
    rows = await ChatUserCMIDs.filter(uid=uid, chat_id=chat_id)
    assert set(row.cmid for row in rows) == set(cmids)
    assert len(rows) == len(cmids)


@pytest.mark.asyncio
async def test_batch_sync_respects_batch_size(db):
    manager = ChatUserCMIDsManager()
    await manager.initialize()

    uid, chat_id = 4, 400
    cmids = list(range(50))

    for cmid in cmids:
        await manager.append_cmid(uid, chat_id, cmid)

    # patch sync to small batch size
    await manager.cache.sync(batch_size=10)

    rows = await ChatUserCMIDs.filter(uid=uid, chat_id=chat_id)
    assert set(row.cmid for row in rows) == set(cmids)
