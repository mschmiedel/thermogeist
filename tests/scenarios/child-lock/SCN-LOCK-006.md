# SCN-LOCK-006: Locking during the unlock time ends it

**Spec:** OVR-023
**Test:** `tests/core/test_child_lock.py::test_locking_during_the_unlock_time_ends_it`

## Initial state
Room child lock on, unlocked for 30 minutes at 18:00.

## Steps
1. At 18:05 someone switches the lock on at the device.

## Expected result
- The unlock time ends (`pause_ended`), the room child lock stays on.

## Why it matters
Whoever is done early does not have to wait for the 30 minutes.
