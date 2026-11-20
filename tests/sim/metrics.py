# SPDX-License-Identifier: MIT
"""Control quality metrics (spec TST-030, list in spec/test-strategy.md)."""

from __future__ import annotations

from itertools import pairwise
from statistics import fmean, pstdev

from .run import Trace

MINUTES_PER_DAY = 24 * 60
SETTLED_BAND_K = 0.3


def window(trace: Trace, start_h: float, end_h: float) -> range:
    return range(int(start_h * 60), min(len(trace.minutes), int(end_h * 60)))


def overshoot_k(trace: Trace, target_c: float) -> float:
    return max(0.0, max(trace.temperatures) - target_c)


def settling_time_h(trace: Trace, target_c: float) -> float | None:
    """First time after which the room stays within ±0.3 K of the target for good."""
    for index in range(len(trace.temperatures)):
        if all(abs(t - target_c) <= SETTLED_BAND_K for t in trace.temperatures[index:]):
            return trace.minutes[index] / 60
    return None


def std_dev_k(trace: Trace, start_h: float, end_h: float) -> float:
    return pstdev(trace.temperatures[i] for i in window(trace, start_h, end_h))


def valve_moves(trace: Trace, start_h: float, end_h: float) -> int:
    indices = list(window(trace, start_h, end_h))
    return sum(1 for a, b in pairwise(indices) if trace.outputs[a] != trace.outputs[b])


def mean_opening_pct(trace: Trace, start_h: float, end_h: float) -> float:
    return fmean(trace.outputs[i] for i in window(trace, start_h, end_h))


def valve_writes(trace: Trace, start_h: float, end_h: float) -> int:
    """Motor movements: how often a new position reached the device."""
    indices = list(window(trace, start_h, end_h))
    return sum(1 for a, b in pairwise(indices) if trace.written[a] != trace.written[b])
