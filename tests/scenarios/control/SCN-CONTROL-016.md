# SCN-CONTROL-016: A thermostat switched off by 5 °C is switched back to heat

**Spec:** ACT-055, ACT-053
**Test:** `tests/ha/test_control.py::test_switched_off_thermostat_is_switched_back_to_heat`

## Initial state
A controlled setpoint thermostat that offers the modes heat and off, room with a window
contact.

## Steps
1. Open the window: Thermogeist writes 5 °C, and the device switches itself to `off` (as Bosch
   Smart Home does).
2. Close the window.

## Expected result
- Thermogeist sets the mode back to `heat` and writes the setpoint again.

## Why it matters
The dining room stayed off after airing: the setpoint written after the window was ignored
while the device was off.
