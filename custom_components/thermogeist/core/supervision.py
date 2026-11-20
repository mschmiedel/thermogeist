# SPDX-License-Identifier: MIT
"""Write verification for valve-based thermostats (spec ACT-043).

Some thermostats keep regulating on their own and overwrite a written valve position. The
supervisor notices that, writes again a limited number of times and then gives up, so
Thermogeist never fights a device endlessly (battery, noise, confusing logbook).
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from enum import StrEnum

DEVIATION_TOLERANCE_PCT = 5.0
DEVIATION_GRACE = timedelta(minutes=5)
MAX_REWRITES_PER_HOUR = 3
REWRITE_WINDOW = timedelta(hours=1)


class Verdict(StrEnum):
    OK = "ok"
    REWRITE = "rewrite"
    GIVE_UP = "give_up"


class ValveSupervisor:
    """Tracks one thermostat's written valve position against what it reports."""

    def __init__(self) -> None:
        self.last_written_pct: float | None = None
        self.last_written_at: datetime | None = None
        self._deviating_since: datetime | None = None
        self._rewrites: deque[datetime] = deque()

    def rewrites_last_hour(self, now: datetime) -> int:
        return sum(1 for t in self._rewrites if now - t < REWRITE_WINDOW)

    def written(self, value_pct: float, now: datetime | None = None) -> None:
        self.last_written_pct = value_pct
        self.last_written_at = now
        self._deviating_since = None

    def check(self, reported_pct: float | None, now: datetime) -> Verdict:
        if self.last_written_pct is None or reported_pct is None:
            return Verdict.OK
        if abs(reported_pct - self.last_written_pct) <= DEVIATION_TOLERANCE_PCT:
            self._deviating_since = None
            return Verdict.OK
        if self._deviating_since is None:
            self._deviating_since = now
        if now - self._deviating_since < DEVIATION_GRACE:
            return Verdict.OK
        while self._rewrites and now - self._rewrites[0] >= REWRITE_WINDOW:
            self._rewrites.popleft()
        if len(self._rewrites) >= MAX_REWRITES_PER_HOUR:
            return Verdict.GIVE_UP
        self._rewrites.append(now)
        self._deviating_since = None
        return Verdict.REWRITE
