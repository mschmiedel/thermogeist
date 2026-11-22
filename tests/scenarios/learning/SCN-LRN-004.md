# SCN-LRN-004: Quiet hours are collected while Home Assistant runs

**Spec:** LRN-030, LRN-031, LRN-036
**Test:** `tests/ha/test_learning.py::test_quiet_hours_are_collected`

## Initial state
A room with a Sonoff (heating at 40 %) at its target of 20 °C, flow 40 °C, cold outside.

## Steps
1. Four hours pass, the room stays at 20.0 °C.
2. Reload the house.

## Expected result
1. At least one observation is stored (the first, started hour does not count, the next one is
   the "hour before").
2. The observations are still there.

## Why it matters
Learning has to work from normal operation, without the user doing anything.
