# SCN-SIZING-006: Hours are collected while running and survive a restart

**Spec:** DIA-014, DIA-015
**Test:** `tests/ha/test_sizing.py::test_hours_are_collected_and_saved`

## Initial state
A heat-pump house with a room whose thermostat reports its valve position; outdoor 2 °C, flow
40 °C, room 19 °C with setpoint 21 °C, the valve reports 100 %.

## Steps
1. Let 61 minutes pass.
2. Save and reload the integration.

## Expected result
- One curve hour and one "fully open in the cold" hour are stored.
- After the reload the sensor attribute `full_open_hours` is still 1.

## Why it matters
Learning across days only works if a restart does not throw the hours away.
