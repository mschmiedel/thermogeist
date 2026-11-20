# SCN-ROOMS-004: Central mode reaches every room

**Spec:** RUL-003, RUL-004
**Test:** `tests/ha/test_rooms.py::test_central_mode_reaches_rooms`

## Initial state
A room with setpoint 20 °C.

## Steps
1. Central mode stop.
2. Central mode frost protection.
3. Central mode auto.

## Expected result
- 1: reason `central_stop`, target and demand unknown.
- 2: reason `frost_protection`, target 7 °C.
- 3: reason `setpoint`, target 20 °C.

## Why it matters
One switch, visible effect in each room.
