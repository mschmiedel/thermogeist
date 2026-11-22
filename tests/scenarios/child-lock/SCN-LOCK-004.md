# SCN-LOCK-004: A device that ignores the lock is asked again later

**Spec:** OVR-022
**Test:** `tests/core/test_child_lock.py::test_a_device_that_ignores_the_lock_is_asked_again_later`

## Initial state
Room child lock on, device unlocked.

## Steps
1. Thermogeist locks it.
2. The device keeps reporting unlocked without any change.

## Expected result
- No new write before 10 minutes (`CHILD_LOCK_RETRY_AFTER`), then one more.

## Why it matters
A device that lost the write gets it again, without a write every minute that drains its battery.
