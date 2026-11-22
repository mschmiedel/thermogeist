# SPDX-License-Identifier: MIT
"""Smart child lock per room (spec OVR-022 to OVR-024).

The room switch is the wish; the devices follow it. A lock switched on at a device is adopted, a
lock that goes off by itself (firmware update, battery change) is set again, and a short unlock
for a battery change ends by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

CHILD_LOCK_UNLOCK = timedelta(minutes=30)
"""OVR-023: long enough for a battery change or a recalibration, short enough to be forgotten."""
CHILD_LOCK_RETRY_AFTER = timedelta(minutes=10)
"""OVR-022: a device that ignored the lock gets it again this often (as ACT-049)."""


class LockState(StrEnum):
    """What a device reports about its child lock."""

    LOCKED = "locked"
    UNLOCKED = "unlocked"
    UNKNOWN = "unknown"


class Change(StrEnum):
    """What a device change meant for the room (OVR-022, OVR-023)."""

    NONE = "none"
    ADOPTED = "adopted"
    """Someone locked a device: the room switch goes on."""
    PAUSE_ENDED = "pause_ended"
    """Someone locked a device during the unlock time: the lock stays on."""
    RESET = "reset"
    """The lock went off by itself while it should be on: it is set again."""


@dataclass(slots=True)
class RoomChildLock:
    """The child lock wish of one room."""

    wanted: bool | None = None
    """None until the room's devices were seen once (OVR-024)."""
    unlocked_until: datetime | None = None

    @property
    def on(self) -> bool:
        return bool(self.wanted)

    def paused(self, now: datetime) -> bool:
        return self.unlocked_until is not None and now < self.unlocked_until

    def set(self, on: bool) -> None:
        self.wanted = on
        self.unlocked_until = None

    def unlock_for_a_while(self, now: datetime) -> datetime:
        """OVR-023: the lock goes off now and on again by itself after the unlock time."""
        self.unlocked_until = now + CHILD_LOCK_UNLOCK
        return self.unlocked_until

    def expire(self, now: datetime) -> bool:
        """OVR-023: True once when the unlock time is over."""
        if self.unlocked_until is None or now < self.unlocked_until:
            return False
        self.unlocked_until = None
        return True

    def first_seen(self, states: list[LockState]) -> bool:
        """OVR-024: a room seen for the first time takes over what its devices show."""
        if self.wanted is not None:
            return False
        known = [s for s in states if s is not LockState.UNKNOWN]
        if not known:
            return False
        self.wanted = LockState.LOCKED in known
        return True

    def device_changed(self, old: LockState, new: LockState, now: datetime) -> Change:
        """OVR-022, OVR-023: interpret a change a device reported."""
        if old is LockState.UNKNOWN or new is LockState.UNKNOWN or old is new:
            return Change.NONE
        if new is LockState.LOCKED:
            if self.paused(now):
                self.unlocked_until = None
                return Change.PAUSE_ENDED
            if not self.wanted:
                self.wanted = True
                return Change.ADOPTED
            return Change.NONE
        if self.wanted and not self.paused(now):
            return Change.RESET
        return Change.NONE

    def should_lock(
        self,
        state: LockState,
        now: datetime,
        written_at: datetime | None,
        *,
        changed_since_write: bool,
    ) -> bool:
        """OVR-022: lock a device that is unlocked although the room wants the lock.

        A change after the last write means the device reset the lock: set it again at once.
        Without news the write is repeated at most every ``CHILD_LOCK_RETRY_AFTER``.
        """
        if not self.wanted or self.paused(now) or state is not LockState.UNLOCKED:
            return False
        if written_at is None or changed_since_write:
            return True
        return now - written_at >= CHILD_LOCK_RETRY_AFTER
