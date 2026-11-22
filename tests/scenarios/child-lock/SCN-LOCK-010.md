# SCN-LOCK-010: Unlocking for 30 minutes survives a restart

**Spec:** OVR-023
**Test:** `tests/ha/test_child_lock.py::test_unlock_for_30_minutes_survives_a_restart`

## Initial state
Room child lock on, device locked.

## Steps
1. Press *Child lock: off for 30 min*.
2. After 10 minutes Thermogeist is reloaded.
3. 20 and 31 minutes after pressing.

## Expected result
- 1. unlocks the device; the room switch stays on and shows `unlocked_until`.
- Nothing is locked before the 30 minutes are over, also not after the reload.
- After 30 minutes the device is locked again; two logbook entries (off until, on again).

## Why it matters
A battery change during a restart does not leave the lock off.
