# SCN-SETPOINT-002: Without external input the device offset is compensated

**Spec:** ACT-052
**Test:** `tests/core/test_setpoint.py::test_offset_compensates_the_device_sensor`

## Initial state
A setpoint thermostat without external input. Target 20 °C, room 19.6 °C, device 22.0 °C
(averaged).

## Steps
1. Compute the device setpoint.
2. Compute it again without a device reading.

## Expected result
- 22.5 °C (20 + 2.4, rounded to 0.5 K): the device aims at 20 °C in the room.
- Without a device reading: 20 °C unchanged.

## Why it matters
Thermostats measure next to the warm radiator and would otherwise stop heating too early.
