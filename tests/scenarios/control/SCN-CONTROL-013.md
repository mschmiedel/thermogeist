# SCN-CONTROL-013: The stored integral is used after Home Assistant restarts

**Spec:** CTL-040
**Test:** `tests/ha/test_restart_and_migration.py::test_integral_is_restored_after_restart`

## Initial state
Stored controller state of the room: integral −4 %, saved just now.

## Steps
1. The house is (re)loaded with a thermostat in the room.

## Expected result
- The planned valve position shows `integral: -4.0`.

## Why it matters
The room continues where it was instead of relearning for hours.
