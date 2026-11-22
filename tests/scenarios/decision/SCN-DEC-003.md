# SCN-DEC-003: A sensor that stays silent is flagged after 6 hours

**Spec:** RUL-013
**Test:** `tests/core/test_decisions.py::test_silent_sensor_is_flagged_after_6_hours`

## Initial state
Sensor last reported at 06:00 and stays available, central mode auto.

## Steps
1. Decide at 11:59:59.
2. Decide at 12:00:00.

## Expected result
- 1: `setpoint` – many sensors report only when the value changes.
- 2: `safety_sensor_stale` with `cause: silent`, `silent_minutes` 360 and `limit_minutes` 360,
  target unchanged.

## Why it matters
With a 60-minute limit six rooms fell to the safe position for up to 5.5 h in a calm night,
because SwitchBot Meter Plus sensors only report changes.
