# SCN-LOCK-003: A lock that went off by itself is set again

**Spec:** OVR-022
**Test:** `tests/core/test_child_lock.py::test_lock_that_went_off_is_set_again`

## Initial state
Room child lock on, the device was locked.

## Steps
1. The device reports unlocked (firmware update, battery change, someone at the device).

## Expected result
- The change counts as a reset; the device is locked again at once.
- With the room child lock off, nothing happens.

## Why it matters
A reset device does not stay open for children without anyone noticing.
