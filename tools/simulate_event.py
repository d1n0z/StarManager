# simulate_real_event.py
from __future__ import annotations
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics

# ---------- CONFIG ----------
@dataclass
class Config:
    n_participants: int = 3000                 # ~3k участников
    mean_cases_per_user: float = 8           # среднее кейсов на человека
    max_cases_per_user: int = 14               # макс кейсов на человека
    expected_total_openings: int = 30000        # ориентир --> можно подогнать
    all_prizes: Dict[int, int] = None          # type: ignore    value -> global limit
    weights: Dict[int, float] = None           # type: ignore    веса при выборе конкретной суммы
    safety: float = 1.0
    min_p: float = 1e-6
    final_threshold: int = 3
    final_boost: float = 5.0
    m_start: float = 0.5
    m_end: float = 4.0
    event_start: datetime = datetime(2025, 12, 20, 18, 0, 0)
    event_end: datetime = datetime(2026, 1, 4, 18, 0, 0)
    random_seed: Optional[int] = None         # Для воспроизводимости; None => случайно

# defaults
cfg = Config()
if cfg.all_prizes is None:
    cfg.all_prizes = {1500: 1, 1000: 1, 700: 1, 500: 1, 300: 1}
if cfg.weights is None:
    cfg.weights = {1500: 3, 1000: 7, 700: 15, 500: 30, 300: 45}
# ---------- end CONFIG ----------


# ---------- helper ----------
def sample_poisson_approx(lmbd: float, max_k: int = 20) -> int:
    import math
    probs = []
    for k in range(0, max_k + 1):
        p = math.exp(-lmbd) * (lmbd ** k) / math.factorial(k)
        probs.append(p)
    total = sum(probs)
    if total < 1.0:
        probs[-1] += (1.0 - total)
    r = random.random()
    cum = 0.0
    for k, p in enumerate(probs):
        cum += p
        if r <= cum:
            return k
    return max_k

def weighted_choice(values: List[int], weights: List[float]) -> int:
    tot = sum(weights)
    if tot <= 0:
        return values[-1]
    r = random.uniform(0, tot)
    acc = 0.0
    for v, w in zip(values, weights):
        acc += w
        if r <= acc:
            return v
    return values[-1]

# ---------- simulator ----------
class RealEventSimulator:
    def __init__(self, config: Config):
        self.cfg = config
        if config.random_seed is not None:
            random.seed(config.random_seed)
        # global state
        self.already_dropped = Counter()   # value -> count already given
        self.openings_done = 0
        self.openings_schedule: List[Tuple[datetime, int]] = []  # list of (time, uid)
        # per-user state
        self.user_cases: Dict[int, int] = {}
        self.user_has_money: Dict[int, bool] = defaultdict(bool)
        # stats
        self.money_drops: Counter = Counter()
        self.non_money_drops: Counter = Counter()
        self.first_money_at_opening_index: Optional[int] = None
        self.exhausted_at_index: Optional[int] = None
        # histories
        self.p_history: List[Tuple[int, datetime, float, int, int]] = []  # (idx, time, p, R, E_rem)
        self.drop_events: List[Tuple[int, datetime, int, int]] = []  # (idx, time, uid, value)

    def generate_users_and_schedule(self):
        start = self.cfg.event_start
        end = self.cfg.event_end
        total_seconds = (end - start).total_seconds()
        uid = 1
        for _ in range(self.cfg.n_participants):
            k = sample_poisson_approx(self.cfg.mean_cases_per_user, max_k=self.cfg.max_cases_per_user)
            k = min(k, self.cfg.max_cases_per_user)
            self.user_cases[uid] = k
            for i in range(k):
                t = start + timedelta(seconds=random.uniform(0, total_seconds))
                self.openings_schedule.append((t, uid))
            uid += 1
        self.openings_schedule.sort(key=lambda x: x[0])
        print(f"Generated {len(self.user_cases)} users, total scheduled openings: {len(self.openings_schedule)}")

    def _calendar_multiplier(self) -> float:
        frac = min(1.0, self.openings_done / self.cfg.expected_total_openings)
        return self.cfg.m_start + (self.cfg.m_end - self.cfg.m_start) * frac

    def _num_money_left_global(self) -> int:
        left_total = 0
        for value, limit in self.cfg.all_prizes.items():
            left_total += max(0, limit - self.already_dropped.get(value, 0))
        return left_total

    def _expected_remaining_openings(self) -> int:
        return max(1, self.cfg.expected_total_openings - self.openings_done)

    def compute_money_probability(self, current_time: datetime) -> float:
        R = self._num_money_left_global()
        E_rem = self._expected_remaining_openings()
        M = self._calendar_multiplier()
        p_raw = (R / E_rem) * self.cfg.safety * M
        if R > 0 and E_rem <= R * self.cfg.final_threshold:
            p_raw = max(p_raw, min(1.0, (R / E_rem) * self.cfg.final_boost))
        p = max(self.cfg.min_p, min(p_raw, 1.0))
        return p

    def sample_money_prize(self) -> Optional[int]:
        available = {}
        for value, limit in sorted(self.cfg.all_prizes.items()):
            left = limit - self.already_dropped.get(value, 0)
            if left > 0:
                available[value] = left
        if not available:
            return None
        values = []
        wts = []
        for v, left in available.items():
            values.append(v)
            wts.append(self.cfg.weights.get(v, 1.0) * left)
        return weighted_choice(values, wts)

    def run(self, stop_when_exhausted: bool = True, verbose: bool = False):
        total_openings = len(self.openings_schedule)
        for idx, (t, uid) in enumerate(self.openings_schedule):
            self.openings_done += 1 # number of openings already happened
            if self.user_cases.get(uid, 0) <= 0:
                continue
            p_money = self.compute_money_probability(t)
            # save history
            R = self._num_money_left_global()
            E_rem = self._expected_remaining_openings()
            self.p_history.append((idx+1, t, p_money, R, E_rem))

            do_money = random.random() <= p_money
            if do_money and (not self.user_has_money.get(uid, False)):
                val = self.sample_money_prize()
                if val is not None:
                    # grant
                    self.already_dropped[val] += 1
                    self.user_has_money[uid] = True
                    self.money_drops[val] += 1
                    self.drop_events.append((idx+1, t, uid, val))
                    if self.first_money_at_opening_index is None:
                        self.first_money_at_opening_index = idx + 1
                    if verbose:
                        print(f"[{idx+1}/{total_openings}] {t.isoformat()} uid={uid} -> MONEY {val} (p={p_money:.6f})")
                    # check exhausted
                    left = self._num_money_left_global()
                    if left == 0:
                        self.exhausted_at_index = idx + 1
                        if verbose:
                            print(f"*** All money prizes exhausted at opening #{self.exhausted_at_index} time={t.isoformat()} ***")
                        if stop_when_exhausted:
                            break
                    self.user_cases[uid] -= 1
                    continue
            # non-money branch (not detailed)
            self.non_money_drops["other"] += 1
            self.user_cases[uid] -= 1
            if verbose and (idx+1) % 2000 == 0:
                print(f"Processed {idx+1}/{total_openings} openings; money so far: {sum(self.money_drops.values())}")

    def report(self, show_drops: bool = True):
        print("\n--- Simulation report ---")
        print(f"Participants: {len(self.user_cases)}")
        total_scheduled = len(self.openings_schedule)
        print(f"Total scheduled openings: {total_scheduled}")
        print(f"Openings processed: {self.openings_done + 1 if total_scheduled>0 else 0}")
        print(f"Money drops total: {sum(self.money_drops.values())}")
        print("Money drops by value:")
        for v, cnt in sorted(self.money_drops.items(), reverse=True):
            print(f"  {v}: {cnt}")
        left = self._num_money_left_global()
        print(f"Left money prizes after sim: {left} (dropped: {dict(self.already_dropped)})")
        if self.exhausted_at_index:
            print(f"Pool exhausted at opening #{self.exhausted_at_index}")
        else:
            print("Pool not exhausted during simulated openings.")
        unique_money_users = len([u for u, got in self.user_has_money.items() if got])
        print(f"Unique users who got money: {unique_money_users}")

        # show some p-history samples
        non_min = [rec for rec in self.p_history if rec[2] > self.cfg.min_p]
        print("\nSample of p-history:")
        for rec in non_min[::int(len(non_min) / 10)]:
            idx, t, p, R, E_rem = rec
            print(f"  idx={idx} date={t.isoformat()} p={p:.6f} R={R} E_rem={E_rem}")
        if non_min:
            print("Last non-min p before exhaustion:", non_min[-1])

        if show_drops:
            print("\nMoney drop events (chronological):")
            for idx, t, uid, val in self.drop_events:
                print(f"  opening #{idx:6d} time={t.isoformat()} uid={uid} -> {val} руб")

# ---------- multi-run helper ----------
def multi_run(base_cfg: Config, n_runs: int = 30, safety_vals: Tuple[float, ...] = (1.0, 1.05, 1.2)):
    print("\n=== Multi-run stability test ===")
    for s in safety_vals:
        exhausted_indices = []
        drops_counts = []
        for seed in range(n_runs):
            cfg2 = Config(**vars(base_cfg))
            cfg2.random_seed = seed + 1000
            cfg2.safety = s
            sim = RealEventSimulator(cfg2)
            sim.generate_users_and_schedule()
            sim.run(stop_when_exhausted=True, verbose=False)
            drops_counts.append(sum(sim.money_drops.values()))
            exhausted_indices.append(sim.exhausted_at_index)
        present = [x for x in exhausted_indices if x is not None]
        mean_idx = statistics.mean(present) if present else None
        drop_mean = statistics.mean(drops_counts)
        drop_stdev = statistics.stdev(drops_counts) if len(drops_counts) > 1 else 0.0
        print(f" safety={s:.2f} -> exhausted in {len(present)}/{n_runs} runs; mean_exhaust_index={mean_idx}; money_drops mean={drop_mean:.2f} stdev={drop_stdev:.2f}")

# ---------- run example ----------
if __name__ == "__main__":
    print("Simulation config:")
    print(cfg)
    # single detailed run
    sim = RealEventSimulator(cfg)
    sim.generate_users_and_schedule()
    sim.run(stop_when_exhausted=True, verbose=False)
    sim.report(show_drops=True)

    # run multi-run (stability) - adjustable
    multi_run(cfg, n_runs=30, safety_vals=(1.0, 1.05, 1.2))
