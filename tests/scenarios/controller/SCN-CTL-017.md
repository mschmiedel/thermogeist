# SCN-CTL-017: Changed valves start the controller fresh

**Spec:** CTL-045, CTL-040
**Test:** `tests/ha/test_restart_and_migration.py::test_changed_valves_start_fresh`

## Initial state
A stored controller state for the room (slow correction −4 %) that belongs to other valves
(a different hardware key).

## Steps
1. Assign a thermostat to the room; the house reloads.

## Expected result
- The stored correction is not used (the integral is not −4 %).

## Why it matters
After replacing a thermostat the old correction held PyM's valve at 95 % for hours although
the room was too warm.
