# SCN-CTL-009: Rounding never makes the valve twitch

**Spec:** CTL-033
**Test:** `tests/core/test_controller.py::test_output_does_not_twitch_on_rounding`

## Initial state
Feed-forward alternating 60.4 / 60.6 %.

## Steps
1. Four steps one minute apart, then 61.2 % ten minutes later (so the rate limit does not interfere).

## Expected result
- Reported: 60, 60, 60, 60, 61.

## Why it matters
Every valve movement costs battery and makes noise.
