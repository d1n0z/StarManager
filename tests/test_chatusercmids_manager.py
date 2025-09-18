# tests/test_chatusercmids_manager.py
import importlib
import pytest


module = importlib.import_module(r"src.StarManager.core.managers.chatusercmids")
pytest_plugins = ("pytest_asyncio",)


class FakeModel:
    """
    Простая in-memory "модель", имитирует методы, которые использует код:
    - all()
    - filter(query)  (мы игнорируем Q и просто возвращаем все)
    - bulk_create(objs)
    Экземпляры: атрибуты uid, chat_id, cmid
    """
    storage = []

    def __init__(self, uid, chat_id, cmid):
        self.uid = uid
        self.chat_id = chat_id
        self.cmid = cmid

    def __repr__(self):
        return f"FakeModel(uid={self.uid}, chat_id={self.chat_id}, cmid={self.cmid})"

    @classmethod
    async def all(cls):
        # возвращаем копию, чтобы тесты не могли нечаянно изменить storage напрямую
        return list(cls.storage)

    @classmethod
    async def filter(cls, _query):
        # игнорируем Q() — возвращаем все записи; код сам отфильтрует по uid/chat_id
        return list(cls.storage)

    @classmethod
    async def bulk_create(cls, objs):
        # вставляем объекты в storage (подразумевается, что objs — список инстансов)
        cls.storage.extend(objs)


@pytest.fixture(autouse=True)
def clear_fake_model_storage():
    FakeModel.storage.clear()
    yield
    FakeModel.storage.clear()


@pytest.mark.asyncio
async def test_initialize_empty(monkeypatch):
    # Подменяем модель в модуле с кодом
    monkeypatch.setattr(module, "ChatUserCMIDs", FakeModel)

    mgr = module.ChatUserCMIDsManager()
    await mgr.initialize()

    # пустой кэш
    got = await mgr.get_cmids(1, 1)
    assert got == ()

@pytest.mark.asyncio
async def test_initialize_with_data(monkeypatch):
    monkeypatch.setattr(module, "ChatUserCMIDs", FakeModel)

    # подготавливаем storage: несколько строк для одной пары и для другой
    FakeModel.storage.extend([
        FakeModel( uid=1, chat_id=10, cmid=100 ),
        FakeModel( uid=1, chat_id=10, cmid=101 ),
        FakeModel( uid=2, chat_id=20, cmid=200 ),
        FakeModel( uid=1, chat_id=10, cmid=100 ),  # дубликат в хранилище
    ])

    mgr = module.ChatUserCMIDsManager()
    await mgr.initialize()

    got = await mgr.get_cmids(1, 10)
    assert set(got) == {100, 101}
    assert isinstance(got, tuple)

    got2 = await mgr.get_cmids(2, 20)
    assert got2 == (200,)

@pytest.mark.asyncio
async def test_append_and_sync_creates_new(monkeypatch):
    monkeypatch.setattr(module, "ChatUserCMIDs", FakeModel)

    mgr = module.ChatUserCMIDsManager()
    await mgr.initialize()

    # append two cmid для пары (1,1)
    await mgr.append_cmid(1, 1, 10)
    await mgr.append_cmid(1, 1, 11)

    # before sync: DB storage still empty
    assert FakeModel.storage == []

    await mgr.sync()

    # После sync — в storage должны появиться 2 записи
    assert len(FakeModel.storage) == 2
    cmids_in_storage = { (r.uid, r.chat_id, r.cmid) for r in FakeModel.storage }
    assert (1,1,10) in cmids_in_storage and (1,1,11) in cmids_in_storage

    # get_cmids вернёт значения из кэша
    got = await mgr.get_cmids(1,1)
    assert set(got) >= {10, 11}

@pytest.mark.asyncio
async def test_no_duplicate_on_existing(monkeypatch):
    monkeypatch.setattr(module, "ChatUserCMIDs", FakeModel)

    # уже есть запись 10
    FakeModel.storage.append(FakeModel(1, 1, 10))

    mgr = module.ChatUserCMIDsManager()
    await mgr.initialize()

    # append duplicate 10 -> не добавится в кэш
    await mgr.append_cmid(1, 1, 10)
    await mgr.append_cmid(1, 1, 11)

    await mgr.sync()

    # storage должно содержать ровно 2 записи: 10 (старое) и 11 (новое)
    assert len(FakeModel.storage) == 2
    cmids = sorted([r.cmid for r in FakeModel.storage if r.uid == 1 and r.chat_id == 1])
    assert cmids == [10, 11]
