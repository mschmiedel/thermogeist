# SCN-CONTROL-011: Window and knob with a setpoint thermostat

**Spec:** ACT-052, ACT-053, OVR-004
**Test:** `tests/ha/test_control.py::test_setpoint_thermostat_window_and_knob`

## Initial state
As SCN-CONTROL-010 with a window contact; the thermostat shows 22.5 °C.

## Steps
1. Open the window for 31 s, then close it.
2. More than 2 minutes later, turn the knob from 22.5 to 23.5 °C and wait a minute.

## Expected result
- Window open: 5 °C at once. Closed: 22.5 °C at once.
- The room setpoint stays 20 °C; Thermogeist writes 22.5 °C back to the thermostat.

## Why it matters
With the setpoint strategy the display and knob are ignored: Thermogeist cannot tell a turned
knob from the device's own schedule or window function.
