# SCN-ROOMS-005: The room setpoint survives a restart

**Spec:** OVR-012
**Test:** `tests/ha/test_rooms.py::test_setpoint_survives_reload`

## Initial state
A room with default setpoint 20 °C.

## Steps
1. Set 21.5 °C on the climate entity.
2. Reload the integration.

## Expected result
- Target stays 21.5 °C.

## Why it matters
A restart must never change what people set.
