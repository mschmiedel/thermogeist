# SCN-HEATER-010: Control mode switches the heater and gives it back

**Spec:** ACT-063, ACT-069
**Test:** `tests/ha/test_heaters.py::test_control_switches_heater_and_restores_it`

## Initial state
A living room at 18 °C (target 20 °C) with a one-stage infrared panel (direct, 1000 W), its
switch off.

## Steps
1. Observe mode for 3 minutes.
2. Control on, after the startup hold.
3. Control off.

## Expected result
1. Nothing is switched; the heater sensor shows the planned stage.
2. The switch is turned on (the room is far too cold).
3. The switch is turned off again – its state before control.

## Why it matters
Users can watch the plan first, and Thermogeist leaves the heater as it found it.
