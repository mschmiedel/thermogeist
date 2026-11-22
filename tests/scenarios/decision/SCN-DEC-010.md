# SCN-DEC-010: An unavailable sensor is flagged after 15 minutes

**Spec:** RUL-013
**Test:** `tests/core/test_decisions.py::test_unavailable_sensor_is_flagged_after_15_minutes`

## Initial state
Sensor reported at 06:00 and has been unavailable since 06:30.

## Steps
1. Decide at 06:44:59.
2. Decide at 06:45:00.

## Expected result
- 1: `setpoint` – a short gap (radio or Zigbee2MQTT restart) does not count.
- 2: `safety_sensor_stale` with `cause: unavailable`, `unavailable_minutes` 15.

## Why it matters
A dead battery or lost radio shows up as unavailable; that has to be caught quickly.
