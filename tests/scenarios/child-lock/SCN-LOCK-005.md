# SCN-LOCK-005: Unlock for 30 minutes ends by itself

**Spec:** OVR-023
**Test:** `tests/core/test_child_lock.py::test_unlock_for_a_while_ends_by_itself`

## Initial state
Room child lock on.

## Steps
1. *Child lock: off for 30 min* is pressed at 18:00.
2. The devices report unlocked.
3. 18:30.

## Expected result
- Until 18:30 nothing is locked again and the unlocked devices are no reset.
- At 18:30 the time is over once and the devices are locked again.

## Why it matters
A battery change does not end with a lock that stays off forever.
