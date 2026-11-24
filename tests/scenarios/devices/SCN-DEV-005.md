# SCN-DEV-005: The setpoint strategy holds a room with a Bosch Smart Home thermostat

**Spec:** TST-012, TST-015, ACT-052, ACT-053
**Test:** `tests/core/test_device_models.py::test_setpoint_strategy_holds_the_room_with_a_shc`

## Initial state
Simulated dining room with a sufficient radiator; the thermostat measures next to the radiator (reads up to 0.4 K warm).

## Steps
1. Run two simulated days.

## Expected result
- Day 2: mean deviation ≤ 0.5 K, at most 0.8 K above the target.
- The valve never goes below the device's own 23 %.
- At most 96 setpoint writes in two days.

## Why it matters
The offset correction lets a device that measures next to the radiator still aim at the right room temperature.
