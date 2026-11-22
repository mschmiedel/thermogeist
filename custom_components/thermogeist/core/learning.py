# SPDX-License-Identifier: MIT
"""Learning stage 1: how much of the modelled demand a room really needs (LRN-030 to LRN-037).

From quiet hours of normal operation (window closed, room steady at its target) the heat the
room received equals its loss. Comparing it with the modelled demand gives one factor per room
(optionally per day and night). No empty or locked room is needed.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from statistics import median

# LRN-030: a quiet hour. The room is near its target and steady, so heat in equals heat out.
QUIET_NEAR_TARGET_K = 0.3
QUIET_MAX_CHANGE_K = 0.2
# Above this outdoor temperature the heating hardly runs and the ratios are noise.
QUIET_MAX_OUTDOOR_C = 15.0
# Each sample of the hour must be quiet; a minute sample rate gives about 60 per hour.
MIN_SAMPLES_PER_HOUR = 45
# LRN-031: below this modelled demand the ratio is dominated by rounding and small gains.
MIN_DEMAND_W = 50.0
# LRN-032: three weeks cover changing weather without keeping old states of the house.
OBSERVATION_WINDOW = timedelta(days=21)
MIN_HOURS = 24
MIN_DAYS = 3
FACTOR_MIN = 0.25
FACTOR_MAX = 3.0
# LRN-033: day and night get their own factor only with enough hours and a clear difference.
PERIOD_MIN_HOURS = 12
PERIOD_DIFFERENCE = 0.25
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6
# LRN-034: a change of the factor by this many percentage points goes to the logbook.
LOGBOOK_CHANGE_PCT = 10.0


class LearningState(StrEnum):
    LEARNING = "learning"
    SETTLED = "settled"
    NOT_ASSESSABLE = "not_assessable"


def is_night(local_hour: int) -> bool:
    """LRN-033: 22 to 6 h local time."""
    return local_hour >= NIGHT_START_HOUR or local_hour < NIGHT_END_HOUR


@dataclass(frozen=True, slots=True)
class Observation:
    hour: datetime
    ratio: float
    """Heat received / modelled demand in this quiet hour."""
    night: bool


@dataclass(frozen=True, slots=True)
class Sample:
    """One minute of a room, as far as learning needs it."""

    quiet: bool
    """Window closed, reason setpoint, sensor fine, flow and valve known, outdoor below 15 °C."""
    room_c: float | None
    target_c: float | None
    received_w: float | None
    demand_w: float | None
    night: bool


@dataclass(slots=True)
class QuietHourCollector:
    """Collects the minute samples of one room and closes one hour at a time."""

    hour: datetime | None = None
    samples: list[Sample] = field(default_factory=list)
    previous_quiet: bool = False
    """LRN-030: the hour before must have been quiet too (e.g. no window)."""

    def add(self, now: datetime, sample: Sample) -> Observation | None:
        """Add a sample; returns an observation when a quiet hour has just finished."""
        hour = now.replace(minute=0, second=0, microsecond=0)
        finished = None
        if self.hour is not None and hour != self.hour:
            finished = self._close()
        if self.hour != hour:
            self.hour = hour
            self.samples = []
        self.samples.append(sample)
        return finished

    def _close(self) -> Observation | None:
        assert self.hour is not None
        observation = quiet_hour_observation(self.hour, self.samples)
        quiet = all_quiet(self.samples)
        result = observation if self.previous_quiet else None
        self.previous_quiet = quiet
        return result


def all_quiet(samples: list[Sample]) -> bool:
    return len(samples) >= MIN_SAMPLES_PER_HOUR and all(s.quiet for s in samples)


def quiet_hour_observation(hour: datetime, samples: list[Sample]) -> Observation | None:
    """LRN-030, LRN-031: the observation of one hour, or None if it was not quiet."""
    if not all_quiet(samples):
        return None
    rooms = [s.room_c for s in samples if s.room_c is not None]
    targets = [s.target_c for s in samples if s.target_c is not None]
    received = [s.received_w for s in samples if s.received_w is not None]
    demands = [s.demand_w for s in samples if s.demand_w is not None]
    if not (rooms and targets and received and demands):
        return None
    if abs(_mean(rooms) - _mean(targets)) > QUIET_NEAR_TARGET_K:
        return None
    if abs(rooms[-1] - rooms[0]) > QUIET_MAX_CHANGE_K:
        return None
    demand = _mean(demands)
    if demand < MIN_DEMAND_W:
        return None
    night = sum(s.night for s in samples) * 2 > len(samples)
    return Observation(hour, _mean(received) / demand, night)


def recent(observations: Iterable[Observation], now: datetime) -> list[Observation]:
    return [o for o in observations if now - o.hour <= OBSERVATION_WINDOW]


@dataclass(frozen=True, slots=True)
class LearnedDemand:
    state: LearningState
    factor: float | None
    """Overall factor (median), None while learning."""
    day: float | None
    night: float | None
    """Own factors per period, only when they differ clearly (LRN-033)."""
    hours: int
    days: int
    spread_pct: float | None
    """Half the interquartile range, in percent of the factor: how much single hours vary."""

    def factor_at(self, night: bool) -> float | None:
        """LRN-034: the factor the feed-forward uses at this time, None while learning."""
        if self.factor is None:
            return None
        own = self.night if night else self.day
        return own if own is not None else self.factor


def _clamp(value: float) -> float:
    return min(FACTOR_MAX, max(FACTOR_MIN, value))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _spread_pct(ratios: list[float], centre: float) -> float | None:
    if len(ratios) < 4 or centre <= 0:
        return None
    ordered = sorted(ratios)
    quarter = len(ordered) // 4
    return round(100 * (ordered[-quarter - 1] - ordered[quarter]) / 2 / centre, 1)


def learned_demand(observations: Iterable[Observation], now: datetime) -> LearnedDemand:
    """LRN-032, LRN-033: the factor from the recent observations."""
    obs = recent(observations, now)
    hours = len(obs)
    days = len({o.hour.date() for o in obs})
    if hours < MIN_HOURS or days < MIN_DAYS:
        return LearnedDemand(LearningState.LEARNING, None, None, None, hours, days, None)
    ratios = [o.ratio for o in obs]
    factor = _clamp(median(ratios))
    day_ratios = [o.ratio for o in obs if not o.night]
    night_ratios = [o.ratio for o in obs if o.night]
    day = night = None
    if len(day_ratios) >= PERIOD_MIN_HOURS and len(night_ratios) >= PERIOD_MIN_HOURS:
        day_factor = _clamp(median(day_ratios))
        night_factor = _clamp(median(night_ratios))
        if abs(day_factor - night_factor) > PERIOD_DIFFERENCE * max(day_factor, night_factor):
            day, night = day_factor, night_factor
    return LearnedDemand(
        LearningState.SETTLED,
        factor,
        day,
        night,
        hours,
        days,
        _spread_pct(ratios, median(ratios)),
    )
