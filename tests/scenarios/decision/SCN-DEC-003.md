# SCN-DEC-003: A silent sensor is flagged after exactly 60 minutes

**Spec:** RUL-013
**Test:** `tests/core/test_decisions.py::test_sensor_becomes_stale_after_60_minutes`

## Initial state
Sensor last reported at 06:00, central mode auto.

## Steps
1. Decide at 06:59:59.
2. Decide at 07:00:00.

## Expected result
- 1: `setpoint`.
- 2: `safety_sensor_stale` with `silent_minutes` 60 and `limit_minutes` 60, target unchanged.

## Why it matters
This is the case that silently throttled the plinth heater before: now it has a name and a time.
