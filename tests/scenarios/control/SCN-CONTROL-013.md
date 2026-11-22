# SCN-CONTROL-013: The stored state is used after Home Assistant restarts

**Spec:** CTL-040
**Test:** `tests/ha/test_restart_and_migration.py::test_integral_is_restored_after_restart`

## Initial state
The running controller of the room has integral −4 % and last plan 46 %.

## Steps
1. The house is reloaded (as after editing a room or restarting Home Assistant).

## Expected result
- The planned valve position shows `integral: -4.0`.
- The plan continues from 46 % (rate-limited), it does not jump.

## Why it matters
The room continues where it was instead of relearning for hours.
