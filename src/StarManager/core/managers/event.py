import asyncio
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, TypeAlias

import loguru
from tortoise.queryset import QuerySet

from StarManager.core import enums, utils
from StarManager.core.managers.base import (
    BaseCachedModel,
    BaseCacheManager,
    BaseManager,
    BaseRepository,
)
from StarManager.core.tables import EventTasks, EventUsers, RewardsPool


@dataclass
class CachedEventTasksRow(BaseCachedModel):
    send_messages_base: int = 25
    send_messages: int = 25
    transfer_coins_base: int = 50
    transfer_coins: int = 50
    rep_users_base: int = 3
    rep_users: int = 3
    win_duels_base: int = 3
    win_duels: int = 3
    level_up_base: int = 1
    level_up: int = 1
    recieved_case: bool = False


@dataclass
class CachedEventUsersRow(BaseCachedModel):
    has_cases: int = 0
    cases_opened: int = 0


@dataclass
class CachedRewardsPoolRow(BaseCachedModel):
    reward_category: enums.RewardCategory
    value: int


@dataclass
class CachedEventRow(BaseCachedModel):
    tasks: Optional[CachedEventTasksRow] = None
    event_user: Optional[CachedEventUsersRow] = None
    rewards: List[CachedRewardsPoolRow] = field(default_factory=list)  # type: ignore


CacheKey: TypeAlias = int
Cache: TypeAlias = Dict[CacheKey, CachedEventRow]


def _make_cache_key(uid: int) -> CacheKey:
    return uid


class EventTasksRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def ensure_record(
        self, uid: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[EventTasks, bool]:
        obj, _created = await EventTasks.get_or_create(uid=uid, defaults=defaults)
        return obj, _created

    def get(self, uid: int) -> QuerySet[EventTasks]:
        return EventTasks.filter(uid=uid)

    async def get_record(self, uid: int) -> Optional[EventTasks]:
        return await self.get(uid).first()

    async def delete_record(self, uid: int):
        await self.get(uid).delete()


class EventUsersRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def ensure_record(
        self, uid: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[EventUsers, bool]:
        obj, _created = await EventUsers.get_or_create(uid=uid, defaults=defaults)
        return obj, _created

    def get(self, uid: int) -> QuerySet[EventUsers]:
        return EventUsers.filter(uid=uid)

    async def get_record(self, uid: int) -> Optional[EventUsers]:
        return await self.get(uid).first()

    async def delete_record(self, uid: int):
        await self.get(uid).delete()


class RewardsPoolRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def ensure_record(
        self, uid: int, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[RewardsPool, bool]:
        obj, _created = await RewardsPool.get_or_create(uid=uid, defaults=defaults)
        return obj, _created

    async def create_record(self, uid: int, reward_category: str, value: int):
        return await RewardsPool.create(
            uid=uid, reward_category=reward_category, value=value
        )

    def get(self, uid: int) -> QuerySet[RewardsPool]:
        return RewardsPool.filter(uid=uid)

    async def get_record(self, uid: int) -> Optional[RewardsPool]:
        return await self.get(uid).first()

    async def delete_record(self, uid: int):
        await self.get(uid).delete()


class EventCache(BaseCacheManager):
    def __init__(
        self,
        event_tasks_repo: EventTasksRepository,
        event_users_repo: EventUsersRepository,
        rewards_pool_repo: RewardsPoolRepository,
        cache: Cache,
        *,
        expected_total_openings: int = 21000,
        money_categories: Optional[Set[enums.RewardCategory]] = None,
        safety: float = 1.1,
        min_p: float = 1e-6,
        final_threshold: int = 3,
        final_boost: float = 5.0,
        m_start: float = 0.5,
        m_end: float = 4.0,
        event_start: Optional[datetime] = None,
        event_end: Optional[datetime] = None,
    ):
        super().__init__()
        self._cache: Cache = cache
        self._dirty: Set[CacheKey] = set()
        self.event_tasks_repo = event_tasks_repo
        self.event_users_repo = event_users_repo
        self.rewards_pool_repo = rewards_pool_repo

        self.rewards_global_pool: List[CachedRewardsPoolRow] = []
        self.already_dropped_counter: Counter[int] = Counter()
        self.openings_so_far: int = 0

        self.expected_total_openings = expected_total_openings

        if money_categories is None:
            money_categories = {
                enums.RewardCategory.money,
            }
        self.money_categories: Set[enums.RewardCategory] = money_categories

        self.all_prizes: Dict[int, int] = {1500: 1, 1000: 1, 700: 1, 500: 1, 300: 1}

        self.safety = safety
        self.min_p = min_p
        self.final_threshold = final_threshold
        self.final_boost = final_boost

        self.m_start = m_start
        self.m_end = m_end

        self.event_start: Optional[datetime] = event_start
        self.event_end: Optional[datetime] = event_end

    async def initialize(self):
        async with self._lock:
            for row in await EventTasks.all():
                self._cache[_make_cache_key(row.uid)] = CachedEventRow(
                    tasks=CachedEventTasksRow.from_model(row)
                )
            for row in await EventUsers.all():
                key = _make_cache_key(row.uid)
                if key not in self._cache:
                    self._cache[key] = CachedEventRow()
                user = CachedEventUsersRow.from_model(row)
                self._cache[key].event_user = user
                self.openings_so_far += user.cases_opened

            for row in await RewardsPool.all():
                key = _make_cache_key(row.uid)
                if key not in self._cache:
                    self._cache[key] = CachedEventRow()
                rwrd = CachedRewardsPoolRow.from_model(row)
                self._cache[key].rewards.append(rwrd)
                self.rewards_global_pool.append(rwrd)
                if rwrd.reward_category in self.money_categories:
                    self.already_dropped_counter[rwrd.value] += 1
        await super().initialize()

    async def sync(self, batch_size: int = 1000):
        async with self._lock:
            if not self._dirty:
                return
            dirty_snapshot = set(self._dirty)
            payloads = {
                key: self._cache[key] for key in dirty_snapshot if key in self._cache
            }

        if not payloads:
            return

        items = list(payloads.items())
        try:
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                uids = list({key for key, _ in batch})

                for table, dataclass_model, alias in (
                    (EventTasks, CachedEventTasksRow, "tasks"),
                    (EventUsers, CachedEventUsersRow, "event_user"),
                ):
                    existing_rows = await table.filter(uid__in=uids).all()
                    keys_set = {k for k, _ in batch}
                    existing_map: Dict[CacheKey, Any] = {
                        _make_cache_key(row.uid): row
                        for row in existing_rows
                        if _make_cache_key(row.uid) in keys_set
                    }

                    to_update = []
                    to_create = []
                    union_changed_fields: Set[str] = set()

                    for key, _ in batch:
                        crow = getattr(payloads[key], alias)
                        if crow is None:
                            continue

                        if key in existing_map:
                            existing_row = existing_map[key]
                            changed_fields = []
                            for k, v in crow.dict().items():
                                if (
                                    not hasattr(existing_row, k)
                                    or getattr(existing_row, k) != v
                                ):
                                    setattr(existing_row, k, v)
                                    changed_fields.append(k)
                            if changed_fields:
                                to_update.append(existing_row)
                                union_changed_fields.update(changed_fields)
                        else:
                            create_kwargs = {"uid": key, **crow.dict()}
                            to_create.append(table(**create_kwargs))

                    if to_update:
                        await table.bulk_update(
                            to_update,
                            fields=list(union_changed_fields),
                            batch_size=batch_size,
                        )

                    if to_create:
                        await table.bulk_create(to_create, batch_size=batch_size)

        except Exception:
            from loguru import logger

            logger.exception("Event sync failed")
            return

        async with self._lock:
            self._dirty -= dirty_snapshot

    async def ensure_by_model(
        self,
        model: type[CachedEventTasksRow | CachedEventUsersRow],
        key: CacheKey,
        defaults: Optional[Dict[str, Any]] = None,
    ):
        if model is CachedEventTasksRow:
            alias = "tasks"
            repo = self.event_tasks_repo
        elif model is CachedEventUsersRow:
            alias = "event_user"
            repo = self.event_users_repo
        else:
            raise ValueError("Invalid model type")
        async with self._lock:
            if key in self._cache and getattr(self._cache[key], alias) is not None:
                return self._cache[key]
        row, _ = await repo.ensure_record(uid=key, defaults=defaults)
        async with self._lock:
            if key not in self._cache:
                self._cache[key] = CachedEventRow(**{alias: model.from_model(row)})  # type: ignore
            else:
                setattr(self._cache[key], alias, model.from_model(row))
            self._dirty.add(key)
            return self._cache[key]

    async def task_progress(
        self, key: CacheKey, type: str, value: int
    ) -> Tuple[CachedEventRow, int, int]:
        await self.ensure_by_model(CachedEventTasksRow, key)
        async with self._lock:
            old_value = getattr(self._cache[key].tasks, type)
            new_value = old_value - value
            if new_value < 0:
                return self._cache[key], old_value, new_value
            setattr(self._cache[key].tasks, type, new_value)
            self._dirty.add(key)
            return self._cache[key], old_value, new_value

    async def edit_cases(self, key: CacheKey, action=1) -> Optional[CachedEventRow]:
        await self.ensure_by_model(CachedEventUsersRow, key)
        async with self._lock:
            self._cache[key].event_user.has_cases += action  # type: ignore
            self._cache[key].tasks.recieved_case = True  # type: ignore
            self._dirty.add(key)

    async def get(self, key: CacheKey) -> Optional[CachedEventRow]:
        async with self._lock:
            return self._cache.get(key, None)

    async def _num_money_left_global(self) -> int:
        left_total = 0
        async with self._lock:
            for value, limit in self.all_prizes.items():
                left_total += max(0, limit - self.already_dropped_counter.get(value, 0))
        return left_total

    def _expected_remaining_openings(self) -> int:
        return max(1, self.expected_total_openings - self.openings_so_far)

    def _day_index_and_days(self) -> Tuple[int, int]:
        if self.event_start and self.event_end:
            total_days = max(
                1, (self.event_end.date() - self.event_start.date()).days + 1
            )
            today = datetime.utcnow().date()
            day_idx = (today - self.event_start.date()).days
            if day_idx < 0:
                day_idx = 0
            if day_idx >= total_days:
                day_idx = total_days - 1
            return day_idx, total_days
        total_days = 100
        frac = min(1.0, self.openings_so_far / max(1, self.expected_total_openings))
        day_idx = int(frac * (total_days - 1))
        return day_idx, total_days

    def _calendar_multiplier(self) -> float:
        day_idx, total_days = self._day_index_and_days()
        if total_days <= 1:
            return self.m_end
        return self.m_start + (self.m_end - self.m_start) * (day_idx / (total_days - 1))

    async def compute_money_probability(self, cached_row: CachedEventRow) -> float:
        R = await self._num_money_left_global()
        E_rem = self._expected_remaining_openings()
        M = self._calendar_multiplier()
        p_raw = (R / E_rem) * self.safety * M
        if R > 0 and E_rem <= R * self.final_threshold:
            p_raw = max(p_raw, min(1.0, (R / E_rem) * self.final_boost))

        loguru.logger.debug(
            f"money_prob R={R} E_rem={E_rem} p={p_raw} openings={self.openings_so_far}"
        )

        return max(self.min_p, min(p_raw, 1.0))

    def sample_money_prize(
        self, *, weights: dict[int, float], all_prizes: Optional[dict[int, int]] = None
    ) -> Optional[int]:
        all_prizes = all_prizes or self.all_prizes
        available = {}
        for value, limit in all_prizes.items():
            left = limit - self.already_dropped_counter.get(value, 0)
            if left > 0:
                available[value] = left
        if not available:
            return None

        values = []
        wts = []
        for value, left in sorted(available.items()):
            values.append(value)
            wts.append(weights.get(value, 1) * left)

        return random.choices(values, weights=wts, k=1)[0]

    async def increment_openings(self, key: CacheKey, n: int = 1):
        async with self._lock:
            self.openings_so_far += 1
            user = self._cache.get(key, None)
            if user and user.event_user:
                user.event_user.cases_opened += n
                self._dirty.add(key)

    async def user_already_got_money(self, key: CacheKey):
        async with self._lock:
            user = self._cache.get(key, None)
            if user is None:
                return False
            for rwd in user.rewards:
                if rwd.reward_category in self.money_categories:
                    return True
            return False

    async def grant_reward(
        self, key: CacheKey, reward_category: enums.RewardCategory, value: int
    ):
        await self.ensure_by_model(CachedEventUsersRow, key)
        await self.rewards_pool_repo.ensure_record(
            key, {"reward_category": reward_category, "value": value}
        )
        async with self._lock:
            rwrd = CachedRewardsPoolRow(
                reward_category=reward_category,
                value=value,
            )
            self._cache[key].rewards.append(rwrd)
            self.rewards_global_pool.append(rwrd)
            if rwrd.reward_category in self.money_categories:
                self.already_dropped_counter[rwrd.value] += 1
            self._dirty.add(key)

    def generate_tasks(self):
        send_messages_base = random.choice((25, 50, 75))
        transfer_coins_base = random.choice((50, 100, 150))
        rep_users_base = random.choice((3, 5, 7))
        win_duels_base = random.choice((3, 5, 7))
        return {
                "send_messages": send_messages_base,
                "send_messages_base": send_messages_base,
                "transfer_coins": transfer_coins_base,
                "transfer_coins_base": transfer_coins_base,
                "rep_users": rep_users_base,
                "rep_users_base": rep_users_base,
                "win_duels": win_duels_base,
                "win_duels_base": win_duels_base,
                "level_up": 1,
                "level_up_base": 1,
            }

    async def drop_tasks(self):
        async with self._lock:
            for key, row in self._cache.items():
                if row.tasks is None:
                    continue
                row.tasks.recieved_case = False
                for k, v in self.generate_tasks().items():
                    setattr(row.tasks, k, v)
                self._dirty.add(key)


class EventManager(BaseManager):
    def __init__(self):
        super().__init__()
        self._cache: Cache = {}
        self.event_tasks_repo = EventTasksRepository()
        self.event_users_repo = EventUsersRepository()
        self.rewards_pool_repo = RewardsPoolRepository()
        self.cache = EventCache(
            self.event_tasks_repo,
            self.event_users_repo,
            self.rewards_pool_repo,
            self._cache,
            expected_total_openings=3000 * 11,
            money_categories={enums.RewardCategory.money},
            safety=1,  #  a "safety" multiplier in case of unsuccessful RNG dispersion (manually boosting money drop chance)
            event_start=datetime(2025, 12, 20, 18),
            event_end=datetime(2026, 1, 4, 18),
        )

        self._open_case_lock = defaultdict(asyncio.Lock)

        self.drop_tasks = self.cache.drop_tasks

    async def generate_tasks(self, uid: int) -> CachedEventTasksRow:
        return (await self.get_user(uid)).tasks  # type: ignore

    async def get_user(self, uid: int) -> CachedEventRow:
        return await self.cache.ensure_by_model(
            CachedEventTasksRow,
            _make_cache_key(uid),
            self.cache.generate_tasks(),
        )

    async def user_already_got_money(self, uid: int) -> bool:
        return await self.cache.user_already_got_money(_make_cache_key(uid))

    async def task_progress(self, uid: int, type: enums.TaskCategory, value: int):
        await self.generate_tasks(uid)
        user, old_value, new_value = await self.cache.task_progress(
            _make_cache_key(uid), type, value
        )
        if (
            user is not None
            and user.tasks is not None
            and all(
                (
                    user.tasks.send_messages <= 0,
                    user.tasks.transfer_coins <= 0,
                    user.tasks.rep_users <= 0,
                    user.tasks.win_duels <= 0,
                    user.tasks.level_up <= 0,
                    not user.tasks.recieved_case,
                )
            )
        ):
            await self.cache.edit_cases(_make_cache_key(uid), +1)

    async def open_case(self, uid: int, chat_id: int):
        async with self._open_case_lock[uid]:
            return await self._open_case(uid, chat_id)

    async def _open_case(self, uid: int, chat_id: int):
        def _get_random_category_no_money(
            prdict: defaultdict[int, int],
        ) -> enums.RewardCategory:
            r = random.random()

            p3, p7, p15, p30, p45 = (
                prdict[3],
                prdict[7],
                prdict[15],
                prdict[30],
                prdict[45],
            )
            if (
                not (p30 < 1 and p45 == 0 and p15 < 2)
                and not (p45 < 1 and p30 == 0 and p15 < 2)
                and p15 >= (1 if p30 > 0 or p45 > 0 else 2)
                and p7 >= (1 if (p30 > 0 or p45 > 0 or p15 > 0) else 2)
                and p3 >= (2 if p30 > 0 or p45 > 0 else 3)
            ):
                if r <= 0.5:
                    return enums.RewardCategory.xp
                else:
                    return enums.RewardCategory.coins

            if r <= 0.425:
                return enums.RewardCategory.xp
            elif r <= 0.85:
                return enums.RewardCategory.coins
            else:
                return enums.RewardCategory.premium

        def _get_random_value_for_category(
            category: enums.RewardCategory,
            rewards: defaultdict[enums.RewardCategory, defaultdict[int, int]],
        ) -> int:
            if category == enums.RewardCategory.premium:
                prdict = rewards[enums.RewardCategory.premium]
                p3, p7, p15, p30, p45 = (
                    prdict[3],
                    prdict[7],
                    prdict[15],
                    prdict[30],
                    prdict[45],
                )
                return random.choices(
                    [3, 7, 15, 30, 45],
                    [
                        0.57 if (p3 < 2 or p30 == p45 == 0) and p3 < 3 else 0,
                        0.3 if (p7 == 0 or p30 == p45 == p15 == 0) and p7 < 2 else 0,
                        0.1 if (p15 == 0 or p30 == p45 == 0) and p15 < 2 else 0,
                        *((0.02, 0.01) if p30 == p45 == 0 and p15 < 2 else (0, 0)),
                    ],
                )[0]
            elif category == enums.RewardCategory.coins:
                codict = rewards[enums.RewardCategory.coins]
                c5, c8, c10, c15 = (
                    codict[500],
                    codict[800],
                    codict[1000],
                    codict[1500],
                )
                return random.choices(
                    [300, 500, 800, 1000, 1500],
                    [
                        0.45,
                        0.3 if c5 < 5 else 0,
                        0.15 if (c8 == 0 or c10 == c15 == 0) and c8 < 2 else 0,
                        *((0.07, 0.03) if c10 == c15 == 0 and c8 < 2 else (0, 0)),
                    ],
                )[0]
            elif category == enums.RewardCategory.xp:
                return random.choices(
                    [3000, 5000, 10000, 15000, 20000], [0.40, 0.35, 0.15, 0.07, 0.03]
                )[0]
            else:
                raise ValueError(f"Unknown category: {category}")

        async def _get_category_value_no_money(
            key: CacheKey,
        ) -> tuple[enums.RewardCategory, int]:
            user = await self.cache.get(key)
            rewards = defaultdict(lambda: defaultdict(int))
            if user is not None and user.rewards:
                for rwrd in user.rewards:
                    rewards[rwrd.reward_category][rwrd.value] += 1

            cat = _get_random_category_no_money(rewards[enums.RewardCategory.premium])
            try:
                return cat, _get_random_value_for_category(cat, rewards)
            except Exception:
                loguru.logger.exception(
                    f"Failed to get value for category: {cat}, uid: {key}!"
                )
                return enums.RewardCategory.xp, 3000

        event_row = await self.cache.get(_make_cache_key(uid))
        if (
            not event_row
            or not event_row.event_user
            or event_row.event_user.has_cases <= 0
        ):
            return f"❄️ [id{uid}|{await utils.get_user_name(uid)}], вы не выполнили все задания."

        await self.cache.edit_cases(_make_cache_key(uid), -1)

        player_rewards = defaultdict(lambda: defaultdict(int))
        for r in event_row.rewards:
            player_rewards[r.reward_category][r.value] += 1

        await self.cache.increment_openings(uid, 1)

        if not await self.user_already_got_money(
            uid
        ) and random.random() <= await self.cache.compute_money_probability(event_row):
            value = self.cache.sample_money_prize(
                weights={1500: 3, 1000: 7, 700: 15, 500: 30, 300: 45},
            )
            if value is not None:
                await self._send_log(uid, chat_id, f"{value} рублей")
                await self.cache.grant_reward(
                    _make_cache_key(uid), enums.RewardCategory.money, value
                )
                return f"🎁 [id{uid}|{await utils.get_user_name(uid)}] получил(-а) денежный приз в размере {value} рублей из особого кейса зимнего ивента (/event)! Администратор свяжется с вами через личные сообщения ВКонтакте."

        category, value = await _get_category_value_no_money(_make_cache_key(uid))

        if category == enums.RewardCategory.premium:
            drop_name = f"премиум-статус на {utils.pluralize_words(value, ('день', 'дня', 'дней'))}"
            await utils.set_premium_status(uid, value, operation="add")
        elif category == enums.RewardCategory.coins:
            drop_name = f"{value} монеток"
            await utils.add_user_coins(uid, value, False)
        else:
            drop_name = f"{value} опыта"
            await utils.add_user_xp(uid, value, False)
        await self._send_log(uid, chat_id, drop_name)
        await self.cache.grant_reward(_make_cache_key(uid), category, value)
        return f"🎁 [id{uid}|{await utils.get_user_name(uid)}] получил(-а) «{drop_name}» из особого кейса зимнего ивента (/event)!"

    async def _send_log(self, uid: int, chat_id: int, drop: str):
        from StarManager.core.config import settings
        from StarManager.tgbot.bot import bot as tgbot

        user = await self.cache.get(_make_cache_key(uid))
        if user is not None and user.event_user is not None:
            cases_opened = user.event_user.cases_opened
        else:
            cases_opened = 1

        date_format = "%d.%m.%Y \\ %H:%M:%S"
        try:
            await tgbot.send_message(
                chat_id=settings.telegram.chat_id,
                message_thread_id=settings.telegram.winter_event_thread_id,
                text=f"""➡️ Открыл кейс — <a href="https://vk.com/id{uid}">{await utils.get_user_name(uid)}</a>
➡️ Беседа: {chat_id}
➡️ Дата открытие: {datetime.now().strftime(date_format)}
➡️ Открыто: {cases_opened}/14
➡️ Приз: {drop}""",
                disable_web_page_preview=True,
                parse_mode="HTML",
            )
        except Exception:
            loguru.logger.exception("Failed to send reward log:")
