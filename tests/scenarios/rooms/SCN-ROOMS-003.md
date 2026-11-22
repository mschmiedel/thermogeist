# SCN-ROOMS-003: A failed room sensor shows up, a quiet one does not

**Spec:** RUL-013, RSN-002
**Test:** `tests/ha/test_rooms.py::test_silent_sensor_is_reported`

## Initial state
A room whose sensor reported at the start.

## Steps
1. Let 5 hours pass without a report (the value did not change).
2. The sensor becomes unavailable; 14 minutes pass.
3. One more minute passes.
4. The sensor reports again.

## Expected result
- 1 and 2: `setpoint`.
- 3: `safety_sensor_stale` with `cause: unavailable`.
- 4: `setpoint` again.

## Why it matters
Safety states are visible and clear themselves when the cause is gone.
