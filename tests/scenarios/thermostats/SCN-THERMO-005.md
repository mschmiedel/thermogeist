# SCN-THERMO-005: The plan follows central stop and a silent sensor

**Spec:** CTL-034, RUL-013
**Test:** `tests/ha/test_thermostats.py::test_plan_follows_stop_and_safety`

## Initial state
As SCN-THERMO-001 after assignment.

## Steps
1. Central mode stop.
2. Central mode auto, then 61 minutes without room temperature.

## Expected result
- 1: planned 0 %, limit `stopped`.
- 2: planned 40 % (minimum opening), limit `safety`.

## Why it matters
Safe states are visible in observe mode already, before anything is controlled.
