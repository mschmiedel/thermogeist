# SCN-CTL-015: After a restart the controller starts from the valve's position

**Spec:** CTL-044
**Test:** `tests/core/test_controller.py::test_seeded_controller_is_rate_limited_from_the_first_step`

## Initial state
Controller seeded with 45 % (reported by the thermostat), heat-pump settings with a 40 % minimum opening.

## Steps
1. First step with feed-forward 64 %.

## Expected result
- Output stays at about 45 %, limit `rate_limit` – no jump. (Below the minimum opening the seed would go up to it at once, CTL-037.)

## Why it matters
Field finding: a restart made the valve jump from 30 to 54 % at once.
