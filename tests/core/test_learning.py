# SPDX-License-Identifier: MIT
"""Learning stage 1 (spec LRN-030 to LRN-033)."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.thermogeist.core.learning import (
    LearningState,
    Observation,
    QuietHourCollector,
    Sample,
    learned_demand,
)

START = datetime(2026, 11, 22, 0, 0, tzinfo=UTC)


def quiet(**overrides: object) -> Sample:
    values: dict[str, object] = {
        "quiet": True,
        "room_c": 21.0,
        "target_c": 21.0,
        "received_w": 150.0,
        "demand_w": 300.0,
        "night": True,
    }
    values.update(overrides)
    return Sample(**values)  # type: ignore[arg-type]


def close(collector: QuietHourCollector, at: datetime) -> Observation | None:
    return collector.add(at, quiet())


def test_only_quiet_hours_are_observed() -> None:
    """Scenario: SCN-LRN-001"""
    collector = QuietHourCollector()
    t = START
    for _ in range(2):
        for minute in range(60):
            observation = collector.add(t + timedelta(minutes=minute), quiet())
        t += timedelta(hours=1)
    observation = close(collector, t)
    assert observation is not None
    assert observation.ratio == pytest.approx(0.5)
    assert observation.night

    window = [quiet()] * 59 + [quiet(quiet=False)]
    for minute, sample in enumerate(window):
        collector.add(t + timedelta(minutes=minute), sample)
    t += timedelta(hours=1)
    assert close(collector, t) is None

    for minute in range(1, 60):
        collector.add(t + timedelta(minutes=minute), quiet())
    t += timedelta(hours=1)
    assert close(collector, t) is None  # the hour before had a window

    for minute in range(1, 60):
        collector.add(t + timedelta(minutes=minute), quiet(room_c=21.5))
    t += timedelta(hours=1)
    assert close(collector, t) is None  # not at its target

    for minute in range(1, 60):
        collector.add(t + timedelta(minutes=minute), quiet(demand_w=40.0))
    t += timedelta(hours=1)
    assert close(collector, t) is None  # demand too small to compare


def observations(
    count: int, ratio: float, *, night: bool = True, days: int = 4
) -> list[Observation]:
    return [
        Observation(START + timedelta(days=i % days, hours=i // days), ratio, night)
        for i in range(count)
    ]


def test_learned_demand_from_observations() -> None:
    """Scenario: SCN-LRN-002"""
    now = START + timedelta(days=5)

    early = learned_demand(observations(20, 0.5), now)
    assert early.state is LearningState.LEARNING
    assert early.factor is None
    assert early.factor_at(night=True) is None

    settled = learned_demand([*observations(30, 0.5), *observations(2, 3.0)], now)
    assert settled.state is LearningState.SETTLED
    assert settled.factor == pytest.approx(0.5)

    assert learned_demand(observations(30, 0.1), now).factor == pytest.approx(0.25)

    split = learned_demand(
        [*observations(15, 0.4, night=True), *observations(15, 0.8, night=False)], now
    )
    assert split.factor_at(night=True) == pytest.approx(0.4)
    assert split.factor_at(night=False) == pytest.approx(0.8)
    similar = learned_demand(
        [*observations(15, 0.5, night=True), *observations(15, 0.55, night=False)], now
    )
    assert similar.night is None
    assert similar.factor_at(night=True) == similar.factor_at(night=False)

    old = learned_demand(observations(30, 0.5), START + timedelta(days=30))
    assert old.hours == 0
