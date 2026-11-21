# SCN-CONTROL-014: The device's own window function is not a turned knob

**Spec:** OVR-005, OVR-001
**Test:** `tests/ha/test_control.py::test_device_window_function_is_not_adopted`

## Initial state
As SCN-CONTROL-011: a setpoint thermostat without external input, room setpoint 20 °C, the
thermostat shows 22.5 °C, the room has a window contact.

## Steps
1. Open the window. Thermogeist writes 5 °C; the device then sets 8 °C on its own.
2. Wait 21 s (longer than the debounce).
3. Close the window. Thermogeist writes 22.5 °C; one second later the device sets its old
   value 8 °C again, then nothing changes for 3 minutes.

## Expected result
- The room setpoint stays 20 °C throughout.
- After the 2-minute grace period Thermogeist writes 22.5 °C again.

## Why it matters
Bosch Room Climate Control lowered its setpoint to 8 °C when the window opened, Thermogeist
took that as a wish and the living room stayed at 8 °C.
