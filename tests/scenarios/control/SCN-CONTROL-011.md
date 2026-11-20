# SCN-CONTROL-011: Window and knob with a setpoint thermostat

**Spec:** ACT-052, ACT-053, OVR-001
**Test:** `tests/ha/test_control.py::test_setpoint_thermostat_window_and_knob`

## Initial state
As SCN-CONTROL-010 with a window contact; the thermostat shows 22.5 °C.

## Steps
1. Open the window for 31 s, then close it.
2. Turn the knob from 22.5 to 23.5 °C and wait 21 s.

## Expected result
- Window open: 5 °C at once. Closed: 22.5 °C at once.
- The room setpoint becomes 21 °C: one degree more, without the offset.

## Why it matters
The device display shows a corrected value; turning the knob must still mean what the user
intends.
