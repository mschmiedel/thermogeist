# SCN-CTL-003: The valve never moves faster than the profile allows

**Spec:** CTL-033
**Test:** `tests/core/test_controller_simulation.py::test_valve_never_moves_faster_than_allowed`

## Initial state
Room as SCN-CTL-001 starting cold at 17 °C.

## Steps
1. Run 4 simulated days and look at every 30-minute window.

## Expected result
- No window changes the valve by more than 10 % (+1 % rounding).

## Why it matters
Slow, predictable valve movements protect the heat pump from sudden flow changes.
