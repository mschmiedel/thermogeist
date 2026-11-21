# SCN-CONTROL-014: The device's own window function is not a turned knob

**Spec:** OVR-005, OVR-001
**Test:** `tests/ha/test_control.py::test_device_window_function_is_not_adopted`

## Initial state
A controlled valve-based Bosch thermostat, room setpoint 20 °C, the room has a window contact.

## Steps
1. Open the window. Thermogeist writes 7 °C; the device then sets 8 °C on its own.
2. Wait 21 s (longer than the debounce).
3. Close the window; the device sets 8 °C again, then nothing changes for 3 minutes.

## Expected result
- The room setpoint stays 20 °C throughout, and nothing about a manual setpoint is logged.
- Thermogeist writes 20 °C to the thermostat again.

## Why it matters
Bosch Room Climate Control lowered its setpoint to 8 °C when the window opened, Thermogeist
took that as a wish and the living room stayed at 8 °C.
