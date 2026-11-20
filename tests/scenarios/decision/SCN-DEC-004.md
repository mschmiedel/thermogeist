# SCN-DEC-004: Safety comes before the central mode

**Spec:** RUL-030
**Test:** `tests/core/test_decisions.py::test_safety_has_precedence_over_central_mode`

## Initial state
Sensor silent for 2 hours, central mode stop.

## Steps
1. Decide.

## Expected result
- Code `safety_sensor_stale`.

## Why it matters
A broken sensor must never hide behind another reason.
