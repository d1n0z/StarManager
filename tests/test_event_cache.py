from collections import Counter
import pytest

# импортируй EventCache и CachedEventRow из твоего модуля
from StarManager.core.managers.event import (
    EventCache,
    CachedEventRow,
    CachedEventUsersRow,
    CachedRewardsPoolRow,
)
from StarManager.core import enums

# ----- Fake repositories (легкие заглушки для тестов) -----
class FakeRepo:
    async def ensure_record(self, uid, defaults=None):
        return (None, False)

    async def create_record(self, uid, reward_category, value):
        return None

    def get(self, uid):
        return None

# ----- Fixtures -----
@pytest.fixture
def event_cache():
    # пустой кэш, fake repos
    cache_dict = {}
    repo = FakeRepo()
    ec = EventCache(repo, repo, repo, cache_dict, expected_total_openings=100)  # type: ignore
    # уменьшает шанс минимально, чтобы предсказуемо проверять p
    ec.safety = 1.0
    # простые призы для теста
    ec.all_prizes = {1500: 1, 1000: 1, 500: 2}
    # reset counters
    ec.already_dropped_counter = Counter()
    ec.openings_so_far = 0
    return ec

# ----- Tests -----
@pytest.mark.asyncio
async def test_compute_money_probability_initial(event_cache):
    ec = event_cache
    # R = 4 (1 +1 +2), E_rem = 100
    R = await ec._num_money_left_global()
    assert R == 4
    p = await ec.compute_money_probability(CachedEventRow())
    # должно быть > 0 и маленькое
    assert 0 < p < 0.1

@pytest.mark.asyncio
async def test_compute_money_probability_final_boost(event_cache):
    ec = event_cache
    # приближаясь к концу: имитируем почти все открытия сделаны
    ec.openings_so_far = 98  # E_rem = 2
    p = await ec.compute_money_probability(CachedEventRow())
    # E_rem <= R * final_threshold => должен примениться final_boost
    assert p > 0.0
    # при таких значениях p может подскочить — проверим что не равно min_p
    assert p > ec.min_p

def test_sample_money_prize_weights_and_availability(event_cache):
    ec = event_cache
    # пока никто не получил ничего
    val = ec.sample_money_prize(weights={1500:3,1000:7,500:45})
    assert val in {1500, 1000, 500}

    # пометить все 1500 и 1000 как уже выданные
    ec.already_dropped_counter[1500] = 1
    ec.already_dropped_counter[1000] = 1
    # осталось только 500 (2 штуки)
    vals = {ec.sample_money_prize(weights={1500:3,1000:7,500:45}) for _ in range(10)}
    assert vals <= {500}

@pytest.mark.asyncio
async def test_grant_reward_and_user_has_money(event_cache):
    ec = event_cache
    key = 123
    # пустой юзер в кэше (создаём вручную)
    ec._cache[key] = CachedEventRow(event_user=CachedEventUsersRow(has_cases=1, cases_opened=0))
    # выдаём приз
    await ec.grant_reward(key, enums.RewardCategory.money, 500)
    # теперь already_dropped_counter должен показать +1
    assert ec.already_dropped_counter[500] >= 1
    # а в кэше у пользователя должен появиться reward-объект
    user = ec._cache[key]
    assert any(r.reward_category == enums.RewardCategory.money for r in user.rewards)

@pytest.mark.asyncio
async def test_user_already_got_money_check(event_cache):
    ec = event_cache
    key = 222
    # пользователь без наград
    ec._cache[key] = CachedEventRow(event_user=CachedEventUsersRow(has_cases=1, cases_opened=0))
    res = await ec.user_already_got_money(key)
    assert res is False
    # добавим денежную награду вручную
    ec._cache[key].rewards.append(CachedRewardsPoolRow(reward_category=enums.RewardCategory.money, value=500))
    res2 = await ec.user_already_got_money(key)
    assert res2 is True
