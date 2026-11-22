# SCN-LOCK-011: Switching on ends the 30 minutes

**Spec:** OVR-023
**Test:** `tests/ha/test_child_lock.py::test_switching_on_ends_the_30_minutes`

## Initial state
Room child lock on, *Child lock: off for 30 min* just pressed (switch shows off).

## Steps
1. Switch *Child lock* on.

## Expected result
- The device is locked at once, the switch shows on, *Child lock back on* is unknown.

## Why it matters
Whoever is done with the battery change locks the room again with the switch they see.
