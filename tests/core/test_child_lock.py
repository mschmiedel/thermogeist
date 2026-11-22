# SPDX-License-Identifier: MIT
"""Smart child lock decisions (spec OVR-022 to OVR-024)."""

from datetime import UTC, datetime, timedelta

from custom_components.thermogeist.core.child_lock import (
    CHILD_LOCK_RETRY_AFTER,
    CHILD_LOCK_UNLOCK,
    Change,
    LockState,
    RoomChildLock,
)

NOW = datetime(2026, 11, 22, 18, 0, tzinfo=UTC)
LOCKED, UNLOCKED, UNKNOWN = LockState.LOCKED, LockState.UNLOCKED, LockState.UNKNOWN


def test_first_seen_takes_over_the_devices() -> None:
    """Scenario: SCN-LOCK-001"""
    waiting = RoomChildLock()
    assert not waiting.first_seen([UNKNOWN])
    assert waiting.wanted is None

    locked = RoomChildLock()
    assert locked.first_seen([UNLOCKED, LOCKED])
    assert locked.on

    unlocked = RoomChildLock()
    assert unlocked.first_seen([UNLOCKED])
    assert unlocked.wanted is False
    assert not unlocked.first_seen([LOCKED])  # only once


def test_lock_at_the_device_is_adopted() -> None:
    """Scenario: SCN-LOCK-002"""
    lock = RoomChildLock(wanted=False)

    assert lock.device_changed(UNLOCKED, LOCKED, NOW) is Change.ADOPTED
    assert lock.on
    assert lock.device_changed(UNKNOWN, LOCKED, NOW) is Change.NONE


def test_lock_that_went_off_is_set_again() -> None:
    """Scenario: SCN-LOCK-003"""
    lock = RoomChildLock(wanted=True)
    written = NOW - timedelta(minutes=1)

    assert lock.device_changed(LOCKED, UNLOCKED, NOW) is Change.RESET
    assert lock.should_lock(UNLOCKED, NOW, written, changed_since_write=True)
    assert not lock.should_lock(LOCKED, NOW, written, changed_since_write=True)

    off = RoomChildLock(wanted=False)
    assert off.device_changed(LOCKED, UNLOCKED, NOW) is Change.NONE
    assert not off.should_lock(UNLOCKED, NOW, None, changed_since_write=False)


def test_a_device_that_ignores_the_lock_is_asked_again_later() -> None:
    """Scenario: SCN-LOCK-004"""
    lock = RoomChildLock(wanted=True)

    assert lock.should_lock(UNLOCKED, NOW, None, changed_since_write=False)
    soon = NOW + CHILD_LOCK_RETRY_AFTER - timedelta(seconds=1)
    assert not lock.should_lock(UNLOCKED, soon, NOW, changed_since_write=False)
    assert lock.should_lock(UNLOCKED, NOW + CHILD_LOCK_RETRY_AFTER, NOW, changed_since_write=False)


def test_unlock_for_a_while_ends_by_itself() -> None:
    """Scenario: SCN-LOCK-005"""
    lock = RoomChildLock(wanted=True)

    until = lock.unlock_for_a_while(NOW)

    assert until == NOW + CHILD_LOCK_UNLOCK
    assert lock.paused(NOW)
    assert lock.device_changed(LOCKED, UNLOCKED, NOW) is Change.NONE
    assert not lock.should_lock(UNLOCKED, NOW, NOW, changed_since_write=True)
    assert not lock.expire(until - timedelta(seconds=1))
    assert lock.expire(until)
    assert not lock.expire(until)
    assert lock.should_lock(UNLOCKED, until, NOW, changed_since_write=True)


def test_locking_during_the_unlock_time_ends_it() -> None:
    """Scenario: SCN-LOCK-006"""
    lock = RoomChildLock(wanted=True)
    lock.unlock_for_a_while(NOW)

    assert lock.device_changed(UNLOCKED, LOCKED, NOW + timedelta(minutes=5)) is Change.PAUSE_ENDED
    assert lock.unlocked_until is None
    assert lock.on
