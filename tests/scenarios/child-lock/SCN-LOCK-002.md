# SCN-LOCK-002: A lock switched on at the device is adopted

**Spec:** OVR-022
**Test:** `tests/core/test_child_lock.py::test_lock_at_the_device_is_adopted`

## Initial state
Room child lock off.

## Steps
1. A device reports locked (it was unlocked before).
2. A device that was unavailable reports locked.

## Expected result
- After 1. the room child lock is on (`adopted`).
- 2. changes nothing: coming back from unavailable is no person's action.

## Why it matters
It does not matter where the lock is switched on: at the device or in Home Assistant.
