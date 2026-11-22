# SCN-LOCK-009: An existing lock is taken over when the thermostat is added

**Spec:** OVR-024
**Test:** `tests/ha/test_child_lock.py::test_existing_lock_is_taken_over`

## Initial state
Sonoff TRVZB with its child lock already on.

## Steps
1. Add it to a room.

## Expected result
- The room child lock is on right away; nothing is written.

## Why it matters
Adding Thermogeist never switches a child lock off.
