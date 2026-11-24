# SCN-DEV-003: The Bosch Smart Home window function closes and reopens

**Spec:** TST-012
**Test:** `tests/core/test_device_models.py::test_shc_window_function_closes_and_reopens`

## Initial state
Model at rest, setpoint and temperature 21 °C.

## Steps
1. Its temperature drops by 1.2 K within a minute.
2. 40 minutes pass at that temperature.

## Expected result
- 1. closes the valve (0 %).
- 2. the valve opens wide again (≥ 50 %): the room is now well below the setpoint.

## Why it matters
The recorded days show this behaviour at every window opening; Thermogeist must not mistake it for its own decision.
