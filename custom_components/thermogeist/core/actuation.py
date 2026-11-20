# SPDX-License-Identifier: MIT
"""When to actually write a valve position to a device (spec ACT-046).

The controller output may change by fractions of a percent every minute. Each write moves a
battery-powered motor, so writes are bundled: bigger steps, less often. Urgent changes (window,
stop, safety) are written at once.
"""

from __future__ import annotations

from datetime import datetime, timedelta

MIN_WRITE_INTERVAL = timedelta(minutes=10)
MIN_WRITE_STEP_PCT = 3.0
# Small remaining differences are still written eventually, so the valve settles exactly.
SETTLE_INTERVAL = timedelta(minutes=30)
SETTLE_STEP_PCT = 1.0


def should_write(
    desired_pct: float,
    last_written_pct: float | None,
    last_written_at: datetime | None,
    now: datetime,
    *,
    urgent: bool = False,
) -> bool:
    """Decide whether a new valve position is worth a motor movement."""
    if last_written_pct is None or last_written_at is None:
        return True
    difference = abs(desired_pct - last_written_pct)
    if difference == 0:
        return False
    if urgent:
        return True
    elapsed = now - last_written_at
    if difference >= MIN_WRITE_STEP_PCT and elapsed >= MIN_WRITE_INTERVAL:
        return True
    return difference >= SETTLE_STEP_PCT and elapsed >= SETTLE_INTERVAL
