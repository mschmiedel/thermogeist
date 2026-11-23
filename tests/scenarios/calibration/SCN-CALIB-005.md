# SCN-CALIB-005: The profile fills in the values

**Spec:** DIA-024
**Test:** `tests/ha/test_calibration.py::test_profile_fills_in_the_values`

## Initial state
Sonoff TRVZB with `closing_steps`.

## Steps
1. Add it to a room.

## Expected result
- The dialog suggests `closing_steps` as calibration status and `0` as value for "not calibrated"; both can be changed or cleared.

## Why it matters
Known models need no input, and everything stays visible and changeable.
