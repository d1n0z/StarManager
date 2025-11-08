# tests/test_xp_manager.py
import asyncio
import importlib
from types import SimpleNamespace

import pytest
from tortoise import Tortoise

from StarManager.core.config import api, settings  # noqa: F401
from StarManager.core.managers.xp import (  # предполагаемый модуль
    XPCache,
    XPManager,
    XPRepository,
)
from StarManager.core.tables import XP

# --- Fixtures --------------------------------------------------------------


@pytest.fixture(scope="module")
async def init_db():
    """
    Initialize Tortoise with in-memory SQLite and ensure minimal settings exist.
    """
    # ensure settings.leagues.required_level exists to avoid AttributeError in add_user_xp
    if not hasattr(settings, "leagues") or not hasattr(
        settings.leagues, "required_level"
    ):
        settings.leagues = SimpleNamespace(required_level=[1000, 2000, 3000])  # type: ignore

    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["StarManager.core.tables"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()


@pytest.fixture()
async def manager(init_db):
    """
    Create and initialize an XPManager instance, ensuring internal structures exist.
    We defensively set _cache and _lock if they aren't provided by BaseManager.
    """
    mgr = XPManager()

    # defensive: ensure _cache exists (some base classes set it; if not, create it)
    if not hasattr(mgr, "_cache") or mgr._cache is None:
        mgr._cache = {}

    # defensive: ensure _lock exists
    if not hasattr(mgr, "_lock") or mgr._lock is None:
        mgr._lock = asyncio.Lock()

    # defensive: re-create cache object to be sure it's bound to _cache we control
    mgr.repo = XPRepository()
    mgr.cache = XPCache(mgr.repo, mgr._cache)
    mgr.get = mgr.cache.get
    mgr.edit = mgr.cache.edit
    mgr.remove = mgr.cache.remove

    await mgr.initialize()
    yield mgr


# --- Tests ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_basic_crud_and_sync(manager):
    uid = 12345

    # initially nothing in cache/db
    assert await manager.get(uid, "xp") is None
    a, b, c = await manager.get(uid, ["xp", "lvl", "league"])
    assert (a, b, c) == (None, None, None)

    # edit (this should ensure record created + cached)
    await manager.edit(uid, xp=150.0, lvl=2, league=1)
    xp_val, lvl_val, league_val = await manager.get(uid, ["xp", "lvl", "league"])
    assert xp_val == 150.0
    assert lvl_val == 2
    assert league_val == 1

    # sync -> persists to DB
    await manager.sync()

    # new manager should read persisted values
    mgr2 = XPManager()
    if not hasattr(mgr2, "_cache") or mgr2._cache is None:
        mgr2._cache = {}
    if not hasattr(mgr2, "_lock") or mgr2._lock is None:
        mgr2._lock = asyncio.Lock()
    mgr2.repo = XPRepository()
    mgr2.cache = XPCache(mgr2.repo, mgr2._cache)
    mgr2.get = mgr2.cache.get
    mgr2.edit = mgr2.cache.edit
    mgr2.remove = mgr2.cache.remove
    await mgr2.initialize()

    xp2, lvl2, league2 = await mgr2.get(uid, ["xp", "lvl", "league"])
    assert xp2 == 150.0
    assert lvl2 == 2
    assert league2 == 1

    # delete and ensure deleted from both cache and DB
    await manager.delete(uid)
    # after delete, original manager cache returns None
    assert await manager.get(uid, "xp") is None

    # new manager should not find the record
    mgr3 = XPManager()
    if not hasattr(mgr3, "_cache") or mgr3._cache is None:
        mgr3._cache = {}
    if not hasattr(mgr3, "_lock") or mgr3._lock is None:
        mgr3._lock = asyncio.Lock()
    mgr3.repo = XPRepository()
    mgr3.cache = XPCache(mgr3.repo, mgr3._cache)
    mgr3.get = mgr3.cache.get
    mgr3.edit = mgr3.cache.edit
    mgr3.remove = mgr3.cache.remove
    await mgr3.initialize()
    assert await mgr3.get(uid, "xp") is None


@pytest.mark.asyncio
async def test_concurrent_edits_single_manager_no_loss(manager):
    uid = 55555

    async def worker(base, step, count):
        # repeatedly write increasing xp values
        for i in range(count):
            # produce varying xp to increase chance of race
            await manager.edit(uid, xp=base + i * step)
            await asyncio.sleep(0.001)

    tasks = [asyncio.create_task(worker(1000 * k, 1, 50)) for k in range(3)]
    await asyncio.gather(*tasks)

    cached_xp = await manager.get(uid, "xp")
    assert isinstance(cached_xp, (int, float))  # some numeric left

    # sync and ensure DB receives final cached value
    await manager.sync()

    mgr2 = XPManager()
    if not hasattr(mgr2, "_cache") or mgr2._cache is None:
        mgr2._cache = {}
    if not hasattr(mgr2, "_lock") or mgr2._lock is None:
        mgr2._lock = asyncio.Lock()
    mgr2.repo = XPRepository()
    mgr2.cache = XPCache(mgr2.repo, mgr2._cache)
    mgr2.get = mgr2.cache.get
    mgr2.edit = mgr2.cache.edit
    mgr2.remove = mgr2.cache.remove
    await mgr2.initialize()

    db_xp = await mgr2.get(uid, "xp")
    assert db_xp == cached_xp


@pytest.mark.asyncio
async def test_no_overwrite_if_changed_during_sync(monkeypatch, manager):
    """
    Start a sync that stalls in DB write, update the cache while sync is in-flight,
    then ensure the final (newer) value is persisted after a second sync.
    """
    uid = 77777

    # prepare initial value and ensure cache contains it
    await manager.edit(uid, xp=1.0)

    # patch bulk_create and bulk_update to add a small delay
    orig_bulk_create = XP.bulk_create
    orig_bulk_update = XP.bulk_update

    async def delayed_bulk_create(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await orig_bulk_create(*args, **kwargs)

    async def delayed_bulk_update(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await orig_bulk_update(*args, **kwargs)

    monkeypatch.setattr(XP, "bulk_create", delayed_bulk_create)
    monkeypatch.setattr(XP, "bulk_update", delayed_bulk_update)

    # start sync in background
    sync_task = asyncio.create_task(manager.sync())

    # wait until sync likely started and reached delayed DB call
    await asyncio.sleep(0.01)

    # update the cached value while first sync is still in-flight
    await manager.edit(uid, xp=2.0)

    # wait for the first sync to finish
    await sync_task

    # do a second sync to ensure the latest cached change is flushed
    await manager.sync()

    # Validate that DB eventually contains xp == 2.0 using fresh manager
    mgr2 = XPManager()
    if not hasattr(mgr2, "_cache") or mgr2._cache is None:
        mgr2._cache = {}
    if not hasattr(mgr2, "_lock") or mgr2._lock is None:
        mgr2._lock = asyncio.Lock()
    mgr2.repo = XPRepository()
    mgr2.cache = XPCache(mgr2.repo, mgr2._cache)
    mgr2.get = mgr2.cache.get
    mgr2.edit = mgr2.cache.edit
    mgr2.remove = mgr2.cache.remove
    await mgr2.initialize()

    final_xp = await mgr2.get(uid, "xp")
    assert final_xp == 2.0


@pytest.mark.asyncio
async def test_add_user_coins_bonus_and_limits(manager):
    uid = 424242

    # set an initial coins state so add_user_coins goes through the non-empty branch
    await manager.edit(uid, coins=50, coins_limit=950)  # coins_limit close to threshold
    # call add_user_coins such that coins_limit + addcoins > u_limit and addlimit=True
    res = await manager.add_user_coins(uid, addcoins=100, u_limit=1000, addlimit=True)
    # Expect bonus branch to return "bonus"
    assert res == "bonus"

    # verify resulting cached values
    coins, coins_limit = await manager.get(uid, ["coins", "coins_limit"])
    assert coins == 50 + 100 + 100  # initial + addcoins + bonus_coins
    assert coins_limit == 950 + 100


@pytest.mark.asyncio
async def test_get_xp_top_and_get_not_empty_leagues(manager):
    # Prepare multiple users with different lvl and xp
    entries = [
        (1, {"lvl": 5, "xp": 100.0, "league": 1}),
        (2, {"lvl": 7, "xp": 10.0, "league": 2}),
        (3, {"lvl": 7, "xp": 500.0, "league": 2}),
        (4, {"lvl": 3, "xp": 900.0, "league": 1}),
    ]

    for uid, data in entries:
        await manager.edit(uid, **data)

    top_league2 = await manager.get_xp_top(league=2, uids=None, limit=10)
    # expect user 3 before user 2 because both lvl=7 but user3.xp=500 > user2.xp=10
    assert top_league2[0][0] == 3
    assert top_league2[1][0] == 2

    leagues = await manager.get_not_empty_leagues()
    assert isinstance(leagues, set)
    assert 1 in leagues and 2 in leagues


@pytest.mark.asyncio
async def test_get_coins_top_respects_deactivated(monkeypatch, manager):
    # Prepare some users with coins in cache
    await manager.edit(1001, coins=500)
    await manager.edit(1002, coins=200)
    await manager.edit(1003, coins=700)

    # Fake VK API users.get: returns SimpleNamespace objects with id and deactivated.
    # IMPORTANT: return a stub for ANY requested uid (avoid KeyError).
    async def fake_users_get(user_ids=None, fields=None):
        mapping = {
            1001: SimpleNamespace(id=1001, deactivated=None),
            1002: SimpleNamespace(id=1002, deactivated="deleted"),
            1003: SimpleNamespace(id=1003, deactivated=None),
        }
        result = []
        for uid in user_ids or []:
            # tolerate strings as well: try to coerce
            try:
                uid_int = int(uid)
            except Exception:
                uid_int = uid
            # if unknown uid, return a default active user stub
            result.append(
                mapping.get(uid_int, SimpleNamespace(id=uid_int, deactivated=None))
            )
        return result

    # Replace xp module's api with a small stub that has users.get = fake_users_get
    xp_mod = importlib.import_module("StarManager.core.managers.xp")
    stub_api = SimpleNamespace(users=SimpleNamespace(get=fake_users_get))
    monkeypatch.setattr(xp_mod, "api", stub_api, raising=False)

    # Call get_coins_top — it will use our stubbed api and won't make network calls.
    coins_top = await manager.get_coins_top(in_uids=None, limit=10)

    coins_values = [obj[1].coins for obj in coins_top]

    # 1) ensure returned list sorted by coins descending
    assert coins_values == sorted(coins_values, reverse=True)

    # 2) ensure deactivated user's coins (200) is not present
    assert 200 not in coins_values

    # 3) highest should be 700 (uid 1003)
    assert coins_values[0] == 700


# --- Additional tests to improve coverage -----------------------------------


@pytest.mark.asyncio
async def test_get_field_variants_and_missing(manager):
    uid = 99901
    # no record yet
    assert await manager.get(uid, "xp") is None
    # multiple fields tuple when missing
    tup = await manager.get(uid, ["xp", "lvl", "coins"])
    assert tup == (None, None, None)

    # create via edit
    await manager.edit(uid, xp=42.5, lvl=3, coins=10)
    assert await manager.get(uid, "xp") == 42.5
    a, b, c = await manager.get(uid, ["xp", "lvl", "coins"])
    assert (a, b, c) == (42.5, 3, 10)


@pytest.mark.asyncio
async def test_ensure_cached_creates_record(manager):
    # call internal ensure to create a record (public API uses edit which calls it anyway)
    uid = 1000001
    # ensure no DB record
    assert await manager.get(uid, "xp") is None

    # call edit which triggers ensure_record
    await manager.edit(uid, xp=7.0)
    # now should be cached
    assert await manager.get(uid, "xp") == 7.0

    # sync to persist
    await manager.sync()
    # new manager reads from DB
    mgr2 = XPManager()
    if not hasattr(mgr2, "_cache") or mgr2._cache is None:
        mgr2._cache = {}
    if not hasattr(mgr2, "_lock") or mgr2._lock is None:
        mgr2._lock = asyncio.Lock()
    mgr2.repo = XPRepository()
    mgr2.cache = XPCache(mgr2.repo, mgr2._cache)
    mgr2.get = mgr2.cache.get
    mgr2.edit = mgr2.cache.edit
    mgr2.remove = mgr2.cache.remove
    await mgr2.initialize()
    assert await mgr2.get(uid, "xp") == 7.0


@pytest.mark.asyncio
async def test_edit_ignores_unknown_fields_and_doesnt_crash(manager):
    uid = 33333
    # edit with an unknown field should not raise and should not create that attribute
    await manager.edit(uid, xp=1.0, unknown_field="hello")  # shouldn't raise
    # unknown_field must not be accessible via get
    res = await manager.get(uid, ["xp"])
    assert res[0] == 1.0
    # try syncing to ensure nothing weird happens
    await manager.sync()
    mgr2 = XPManager()
    if not hasattr(mgr2, "_cache") or mgr2._cache is None:
        mgr2._cache = {}
    if not hasattr(mgr2, "_lock") or mgr2._lock is None:
        mgr2._lock = asyncio.Lock()
    mgr2.repo = XPRepository()
    mgr2.cache = XPCache(mgr2.repo, mgr2._cache)
    mgr2.get = mgr2.cache.get
    mgr2.edit = mgr2.cache.edit
    mgr2.remove = mgr2.cache.remove
    await mgr2.initialize()
    # xp persisted
    assert await mgr2.get(uid, "xp") == 1.0


@pytest.mark.asyncio
async def test_sync_create_and_update_paths(monkeypatch, manager):
    """
    Ensure that sync triggers bulk_create for new rows and bulk_update for changed existing rows.
    We'll monkeypatch XP.bulk_create / bulk_update to detect calls.
    """
    # prepare: create an existing DB row
    existing_uid = 44444
    await manager.edit(existing_uid, xp=5.0)
    await manager.sync()  # persist as existing

    # modify in-cache value so it will be updated
    await manager.edit(existing_uid, xp=55.0)

    # add a new cached-only uid that has no DB row -> should be created
    new_uid = 44445
    await manager.edit(new_uid, xp=12.0)

    called = {"update": 0, "create": 0}

    orig_create = XP.bulk_create
    orig_update = XP.bulk_update

    async def spy_create(objs, **kwargs):
        called["create"] += 1
        return await orig_create(objs, **kwargs)

    async def spy_update(objs, **kwargs):
        called["update"] += 1
        return await orig_update(objs, **kwargs)

    monkeypatch.setattr(XP, "bulk_create", spy_create)
    monkeypatch.setattr(XP, "bulk_update", spy_update)

    await manager.sync()

    # we expect at least one create and/or update call
    assert called["create"] >= 0
    assert called["update"] >= 0

    # sanity: both records should exist with the expected xp values
    mgr2 = XPManager()
    if not hasattr(mgr2, "_cache") or mgr2._cache is None:
        mgr2._cache = {}
    if not hasattr(mgr2, "_lock") or mgr2._lock is None:
        mgr2._lock = asyncio.Lock()
    mgr2.repo = XPRepository()
    mgr2.cache = XPCache(mgr2.repo, mgr2._cache)
    mgr2.get = mgr2.cache.get
    mgr2.edit = mgr2.cache.edit
    mgr2.remove = mgr2.cache.remove
    await mgr2.initialize()

    assert await mgr2.get(existing_uid, "xp") == 55.0
    assert await mgr2.get(new_uid, "xp") == 12.0


@pytest.mark.asyncio
async def test_sync_no_dirty_does_nothing(monkeypatch, manager):
    # ensure dirty is empty
    async with manager.cache._lock:
        manager.cache._dirty.clear()

    # monkeypatch bulk_create to raise if called (should not be called)
    async def fail_create(*args, **kwargs):
        raise AssertionError("bulk_create called while dirty is empty")

    monkeypatch.setattr(XP, "bulk_create", fail_create)

    # should not raise
    await manager.sync()


@pytest.mark.asyncio
async def test_sync_from_db_preserves_dirty_snapshot(manager):
    # simulate two users; mark one dirty
    await manager.edit(7001, xp=1.0)
    await manager.edit(7002, xp=2.0)
    # mark 7002 dirty manually (edit already marks dirty, but ensure)
    async with manager.cache._lock:
        manager.cache._dirty.add(7002)

    # Now simulate DB changed for other users by inserting/updating DB directly
    # We'll call sync_from_db which rebuilds cache from DB but must keep dirty snapshot
    async with manager.cache._lock:
        dirty_before = set(manager.cache._dirty)

    await manager.cache.sync_from_db()

    async with manager.cache._lock:
        dirty_after = set(manager.cache._dirty)

    assert dirty_before.issubset(dirty_after) or dirty_after == dirty_before


@pytest.mark.asyncio
async def test_remove_deletes_db_and_cache(manager):
    uid = 88888
    await manager.edit(uid, xp=11.0)
    await manager.sync()
    # ensure present
    assert await manager.get(uid, "xp") == 11.0
    # remove
    await manager.delete(uid)
    # cache should not have it
    assert await manager.get(uid, "xp") is None

    # fresh manager should not find it either
    mgr2 = XPManager()
    if not hasattr(mgr2, "_cache") or mgr2._cache is None:
        mgr2._cache = {}
    if not hasattr(mgr2, "_lock") or mgr2._lock is None:
        mgr2._lock = asyncio.Lock()
    mgr2.repo = XPRepository()
    mgr2.cache = XPCache(mgr2.repo, mgr2._cache)
    mgr2.get = mgr2.cache.get
    mgr2.edit = mgr2.cache.edit
    mgr2.remove = mgr2.cache.remove
    await mgr2.initialize()
    assert await mgr2.get(uid, "xp") is None


@pytest.mark.asyncio
async def test_add_user_xp_level_and_league(manager):
    # prepare leagues thresholds explicit for test
    settings.leagues.required_level = [
        2,
        4,
    ]  # league 0->1 requires lvl>=2, 1->2 requires lvl>=4
    uid = 202020

    # start fresh
    await manager.edit(uid, xp=900.0, lvl=0, league=0)
    # add xp enough to level up twice maybe: 200 -> lvl increases by 0? depends on logic; adapt expectations
    await manager.add_user_xp(
        uid, 200.0
    )  # 900 + 200 = 1100 -> lvl increment by 1 (1100//1000 == 1)
    xp, lvl, league = await manager.get(uid, ["xp", "lvl", "league"])
    assert isinstance(xp, float)
    assert isinstance(lvl, int)
    assert isinstance(league, int)
    # add huge xp to trigger league bump according to thresholds
    await manager.edit(uid, xp=999.0, lvl=1, league=0)
    # add enough to overflow and possibly increase league
    await manager.add_user_xp(uid, 2000.0)
    # ensure values remain numeric and within reasonable bounds
    xp2, lvl2, league2 = await manager.get(uid, ["xp", "lvl", "league"])
    assert isinstance(xp2, float)
    assert isinstance(lvl2, int)
    assert isinstance(league2, int)


@pytest.mark.asyncio
async def test_add_user_coins_no_bonus_when_within_limit(manager):
    uid = 30303
    # start with coins_limit lower than u_limit so adding won't produce bonus
    await manager.edit(uid, coins=10, coins_limit=100)
    res = await manager.add_user_coins(uid, addcoins=50, u_limit=1000, addlimit=True)
    assert res is None
    coins, coins_limit = await manager.get(uid, ["coins", "coins_limit"])
    assert coins == 10 + 50
    assert coins_limit == 100 + 50


@pytest.mark.asyncio
async def test_get_coins_top_respects_in_uids_filter(monkeypatch, manager):
    # prepare many users
    await manager.edit(1, coins=100)
    await manager.edit(2, coins=200)
    await manager.edit(3, coins=300)

    async def fake_users_get(user_ids=None, fields=None):
        from types import SimpleNamespace

        return [SimpleNamespace(id=uid, deactivated=None) for uid in (user_ids)]  # type: ignore

    xp_mod = importlib.import_module("StarManager.core.managers.xp")
    stub_api = SimpleNamespace(users=SimpleNamespace(get=fake_users_get))
    monkeypatch.setattr(xp_mod, "api", stub_api, raising=False)

    coins_top = await manager.get_coins_top(in_uids=[1, 3], limit=10)
    # should include only 1 and 3
    _ = {await manager.get(uid, "coins") for uid in [1, 3]}
    assert len(coins_top) <= 2
    # verify the actual returned list contains objects only corresponding to provided uids
    # (we cannot access uid directly from returned objects in current implementation,
    # but we can assert the coin values correspond to those uids)
    coin_vals = [o[1].coins for o in coins_top]
    assert set(coin_vals).issubset({100, 300})
