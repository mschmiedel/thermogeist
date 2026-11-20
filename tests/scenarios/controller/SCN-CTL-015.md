# SCN-CTL-015: After a restart the controller starts from the valve's position

**Spec:** CTL-044
**Test:** `tests/core/test_controller.py::test_seeded_controller_is_rate_limited_from_the_first_step`

## Initial state
Controller seeded with 30 % (reported by the thermostat).

## Steps
1. First step with feed-forward 54 %.

## Expected result
- Output stays at 30 %, limit `rate_limit` – no jump.

## Why it matters
Field finding: a restart made the valve jump from 30 to 54 % at once.
