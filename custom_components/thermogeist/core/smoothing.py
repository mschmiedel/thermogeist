# SPDX-License-Identifier: MIT
"""Moving average for noisy inputs such as the flow temperature (spec CTL-038, CTL-039)."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta

FLOW_WINDOW = timedelta(minutes=30)
FLOW_PLAUSIBLE_MIN_C = 5.0
FLOW_PLAUSIBLE_MAX_C = 70.0


class MovingAverage:
    """Mean of the samples of the last ``window``. Samples come in irregularly."""

    def __init__(self, window: timedelta = FLOW_WINDOW) -> None:
        self._window = window
        self._samples: deque[tuple[datetime, float]] = deque()

    def add(self, now: datetime, value: float) -> None:
        self._samples.append((now, value))
        self._drop_old(now)

    def value(self, now: datetime) -> float | None:
        self._drop_old(now)
        if not self._samples:
            return None
        return sum(v for _, v in self._samples) / len(self._samples)

    def _drop_old(self, now: datetime) -> None:
        while self._samples and now - self._samples[0][0] > self._window:
            self._samples.popleft()


def plausible_flow(value: float | None) -> bool:
    """CTL-039: values outside 5-70 °C are sensor errors, not heating water."""
    return value is not None and FLOW_PLAUSIBLE_MIN_C <= value <= FLOW_PLAUSIBLE_MAX_C
