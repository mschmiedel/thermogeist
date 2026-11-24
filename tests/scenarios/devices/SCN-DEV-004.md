# SCN-DEV-004: The setpoint strategy holds a room with a BTH-RA

**Spec:** TST-012, TST-015, ACT-051
**Test:** `tests/core/test_device_models.py::test_setpoint_strategy_holds_the_room_with_a_bth_ra`

## Initial state
Simulated small bathroom, radiator with margin, outdoor 0 °C, flow 40 °C, target 20.5 °C; the thermostat gets the room temperature (external input).

## Steps
1. Run two simulated days.

## Expected result
- Day 2 never more than 0.5 K above the target, mean deviation ≤ 0.3 K.
- The target is sent at most twice: no chasing.

## Why it matters
With an external temperature input, sending the room target is enough: the device's integrating controller does the rest.
