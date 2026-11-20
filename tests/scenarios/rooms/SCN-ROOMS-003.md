# SCN-ROOMS-003: A silent room sensor shows up after 60 minutes

**Spec:** RUL-013, RSN-002
**Test:** `tests/ha/test_rooms.py::test_silent_sensor_is_reported`

## Initial state
A room whose sensor reported at the start.

## Steps
1. Let 59 minutes pass.
2. Let one more minute pass.
3. The sensor reports again.

## Expected result
- 1: `setpoint`.
- 2: `safety_sensor_stale`.
- 3: `setpoint` again.

## Why it matters
Safety states are visible and clear themselves when the cause is gone.
