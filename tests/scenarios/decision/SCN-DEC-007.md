# SCN-DEC-007: After a restart the room shows that writes are paused

**Spec:** ACT-045
**Test:** `tests/core/test_decisions.py::test_startup_hold_is_shown_until_writes_start`

## Initial state
Home Assistant started less than 90 s ago.

## Steps
1. Decide.

## Expected result
- Code `startup_hold`, target is the user setpoint.

## Why it matters
Users see why nothing happens right after a restart.
