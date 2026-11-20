# SCN-CONTROL-010: A setpoint thermostat is controlled and aims at the room temperature

**Spec:** ACT-044, ACT-050, ACT-052, ACT-054
**Test:** `tests/ha/test_control.py::test_setpoint_thermostat_aims_at_the_room_temperature`

## Initial state
A room at 19.5 °C, target 20 °C, with one unknown thermostat: no valve access, no external
temperature input. The thermostat measures 22.0 °C next to the radiator.

## Steps
1. Switch control on; wait for the 90 s start-up hold.
2. Switch control off.

## Expected result
- The thermostat gets 22.5 °C (20 °C + 2.5 K offset), no valve writes.
- The thermostat shows `strategy: automatic`, `last_write_value: 22.5`, `setpoint_offset: 2.5`.
- When switched off, it gets the plain room setpoint 20 °C back.

## Why it matters
Thermostats without valve access can be controlled too, and still aim at the right room
temperature.
