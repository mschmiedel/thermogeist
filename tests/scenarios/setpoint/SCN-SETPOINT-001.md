# SCN-SETPOINT-001: With an external temperature input the room target is sent

**Spec:** ACT-051
**Test:** `tests/core/test_setpoint.py::test_external_input_sends_the_room_target`

## Initial state
A setpoint thermostat that receives the room temperature. Target 21 °C, room 19 °C, device 24 °C.

## Steps
1. Compute the device setpoint.

## Expected result
- 21 °C: the device regulates on the real room temperature, no correction needed.

## Why it matters
The device's own reading next to the radiator must not distort the target.
