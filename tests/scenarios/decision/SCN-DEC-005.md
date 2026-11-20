# SCN-DEC-005: A sensor that never reported counts as stale

**Spec:** RUL-013
**Test:** `tests/core/test_decisions.py::test_never_reported_is_stale`

## Initial state
No valid temperature ever received.

## Steps
1. Decide.

## Expected result
- Code `safety_sensor_stale` without `silent_minutes`.

## Why it matters
A wrongly selected sensor entity is noticed instead of being ignored.
