# SPDX-License-Identifier: MIT
from datetime import UTC, datetime, timedelta

from custom_components.thermogeist.core.supervision import ValveSupervisor, Verdict
from custom_components.thermogeist.core.time_provider import FakeTimeProvider

START = datetime(2026, 12, 1, tzinfo=UTC)


def test_small_or_short_deviations_are_tolerated() -> None:
    """Scenario: SCN-SUP-001"""
    clock = FakeTimeProvider(START)
    supervisor = ValveSupervisor()
    supervisor.written(40.0)

    assert supervisor.check(44.0, clock.now()) is Verdict.OK
    assert supervisor.check(14.0, clock.now()) is Verdict.OK
    clock.advance(timedelta(minutes=4, seconds=59))
    assert supervisor.check(14.0, clock.now()) is Verdict.OK
    clock.advance(timedelta(seconds=1))
    assert supervisor.check(14.0, clock.now()) is Verdict.REWRITE


def test_gives_up_after_three_rewrites_within_an_hour() -> None:
    """Scenario: SCN-SUP-002"""
    clock = FakeTimeProvider(START)
    supervisor = ValveSupervisor()
    supervisor.written(40.0)
    verdicts = []
    for _ in range(4):
        supervisor.check(14.0, clock.now())
        clock.advance(timedelta(minutes=5))
        verdict = supervisor.check(14.0, clock.now())
        verdicts.append(verdict)
        if verdict is Verdict.REWRITE:
            supervisor.written(40.0)
    assert verdicts == [Verdict.REWRITE, Verdict.REWRITE, Verdict.REWRITE, Verdict.GIVE_UP]


def test_rewrites_age_out_after_an_hour() -> None:
    """Scenario: SCN-SUP-003"""
    clock = FakeTimeProvider(START)
    supervisor = ValveSupervisor()
    for _ in range(3):
        supervisor.written(40.0)
        supervisor.check(14.0, clock.now())
        clock.advance(timedelta(minutes=5))
        assert supervisor.check(14.0, clock.now()) is Verdict.REWRITE

    clock.advance(timedelta(hours=1))
    supervisor.written(40.0)
    supervisor.check(14.0, clock.now())
    clock.advance(timedelta(minutes=5))
    assert supervisor.check(14.0, clock.now()) is Verdict.REWRITE
