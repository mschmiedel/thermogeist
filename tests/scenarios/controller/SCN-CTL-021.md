# SCN-CTL-021: After the safe position the controller does not ramp down from it

**Spec:** CTL-034
**Test:** `tests/core/test_controller.py::test_safe_position_is_no_starting_point`

## Initial state
Heat-pump profile (minimum 40 %, max. 10 % per 30 minutes), target 19.5 °C. The room is
1.5 K too warm, the plan is at its lowest.

## Steps
1. A restart: the first step has no room temperature yet.
2. One minute later the room temperature is there again, still 1.5 K too warm.

## Expected result
1. The safe position (40 %), limit `safety`.
2. Straight back to the computed position below the minimum, without `rate_limit`.

## Why it matters
After a restart Roy's plan crept down from 30 % to 0 % for 1.5 hours while a gaming PC
already kept the room too warm.
