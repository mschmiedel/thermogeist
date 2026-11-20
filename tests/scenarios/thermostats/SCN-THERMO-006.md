# SCN-THERMO-006: The plan is right immediately after a restart

**Spec:** CTL-033, CTL-034
**Test:** `tests/ha/test_thermostats.py::test_plan_is_correct_right_after_restart`

## Initial state
As SCN-THERMO-001 after assignment; the central mode `auto` is restored on start-up.

## Steps
1. Reload the integration (like a Home Assistant restart).

## Expected result
- The planned position is ≈ 68 % again, not stuck at the safe 40 %.
- The active reason never shows `safety_sensor_stale` during the restart (no false entry in the logbook).

## Why it matters
Restoring the central mode used to trigger a calculation before room temperatures were read.
The controller then started from a false safe state, and the rate limit kept it there; the
logbook briefly showed "temperature sensor silent".
