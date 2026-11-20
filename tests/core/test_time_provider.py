# SPDX-License-Identifier: MIT
from datetime import UTC, datetime, timedelta, timezone

import pytest

from custom_components.thermogeist.core.time_provider import (
    FakeTimeProvider,
    SystemTimeProvider,
)

START = datetime(2026, 11, 20, 6, 0, tzinfo=UTC)


def test_advance_moves_both_clocks() -> None:
    """Scenario: SCN-TIME-001"""
    clock = FakeTimeProvider(START)

    clock.advance(timedelta(minutes=90))
    clock.advance(timedelta(days=2))

    assert clock.now() == datetime(2026, 11, 22, 7, 30, tzinfo=UTC)
    assert clock.monotonic() == timedelta(days=2, minutes=90).total_seconds()


def test_negative_advance_is_rejected() -> None:
    """Scenario: SCN-TIME-002"""
    clock = FakeTimeProvider(START)

    with pytest.raises(ValueError):
        clock.advance(timedelta(seconds=-1))

    assert clock.now() == START
    assert clock.monotonic() == 0.0


def test_start_time_must_be_timezone_aware() -> None:
    """Scenario: SCN-TIME-003"""
    with pytest.raises(ValueError):
        FakeTimeProvider(datetime(2026, 11, 20, 6, 0))

    plus_one = timezone(timedelta(hours=1))
    clock = FakeTimeProvider(datetime(2026, 11, 20, 7, 0, tzinfo=plus_one))

    assert clock.now() == START
    assert clock.now().tzinfo == UTC


def test_system_time_provider_is_aware_and_monotonic() -> None:
    clock = SystemTimeProvider()

    assert clock.now().tzinfo is not None
    first = clock.monotonic()
    assert clock.monotonic() >= first
