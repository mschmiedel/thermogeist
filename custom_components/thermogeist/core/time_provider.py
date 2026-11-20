# SPDX-License-Identifier: MIT
"""Time abstraction for the core (spec TST-001 to TST-003).

Domain logic never reads the clock directly. It receives a ``TimeProvider`` so that learning,
debouncing and timeouts can be tested deterministically over simulated days and weeks.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Protocol


class TimeProvider(Protocol):
    """Source of time for the core."""

    def now(self) -> datetime:
        """Return the current wall-clock time, timezone-aware, in UTC."""
        ...

    def monotonic(self) -> float:
        """Return a monotonic clock in seconds, for measuring durations."""
        ...


class SystemTimeProvider:
    """Real clock, used in production."""

    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()


class FakeTimeProvider:
    """Controllable clock for tests and the simulator.

    Time only moves when ``advance`` is called, and it never moves backwards.
    """

    def __init__(self, start: datetime) -> None:
        _require_aware(start)
        self._now = start.astimezone(UTC)
        self._monotonic = 0.0

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._monotonic

    def advance(self, delta: timedelta) -> None:
        """Move time forward by ``delta``. Negative deltas are rejected."""
        if delta < timedelta(0):
            raise ValueError("time cannot move backwards")
        self._now += delta
        self._monotonic += delta.total_seconds()


def _require_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("naive datetime: a timezone is required")
