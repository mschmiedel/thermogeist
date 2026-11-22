# SCN-LRN-001: Only quiet hours become observations

**Spec:** LRN-030, LRN-031
**Test:** `tests/core/test_learning.py::test_only_quiet_hours_are_observed`

## Initial state
A room held at 21.0 °C (target 21.0 °C); radiators and devices give 150 W, the model expects
300 W.

## Steps
1. A quiet hour after a quiet hour.
2. An hour with one minute not quiet (a window).
3. A quiet hour right after it.
4. A quiet hour in which the room is 0.5 K above its target, and one with a modelled demand
   of 40 W.

## Expected result
1. Observation with ratio 0.5.
2. None.
3. None – the hour before was not quiet.
4. None for both.

## Why it matters
Only hours in which heat in equals heat out tell what the room really needs.
