# SPDX-License-Identifier: MIT
"""Lost calibration, from what the device reports (spec DIA-024).

Which value means "not calibrated" is device data in the profile (role ``calibration_status``
with ``uncalibrated`` values), never code: Sonoff TRVZB reports ``closing_steps`` 0, Bosch
BTH-RA a ``valve_adapt_status`` such as ``ready_to_calibrate``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

CALIBRATION_LOST_AFTER = timedelta(minutes=10)
"""DIA-024: a calibration takes about a minute and passes through these values; only a state
that lasts this long is reported."""


def is_uncalibrated(state: str | None, uncalibrated: Iterable[str]) -> bool | None:
    """True if the reported value means "not calibrated"; None while nothing is known.

    Numbers are compared by value: Home Assistant may report "0.0" for 0.
    """
    if state is None:
        return None
    for value in uncalibrated:
        if state.casefold() == value.casefold():
            return True
        try:
            if float(state) == float(value):
                return True
        except ValueError:
            continue
    return False


@dataclass(slots=True)
class CalibrationWatch:
    """One thermostat: is it lost, and since when does it look like it."""

    since: datetime | None = None
    lost: bool = False

    def update(self, uncalibrated: bool | None, now: datetime) -> bool:
        """Feed the current reading; True when ``lost`` changed."""
        if uncalibrated is None:
            return False
        if not uncalibrated:
            self.since = None
            if self.lost:
                self.lost = False
                return True
            return False
        if self.since is None:
            self.since = now
        if not self.lost and now - self.since >= CALIBRATION_LOST_AFTER:
            self.lost = True
            return True
        return False
