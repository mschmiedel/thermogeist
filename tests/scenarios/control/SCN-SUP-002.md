# SCN-SUP-002: After three rewrites in an hour Thermogeist gives up

**Spec:** ACT-043
**Test:** `tests/core/test_supervision.py::test_gives_up_after_three_rewrites_within_an_hour`

## Initial state
40 % written, the device keeps going back to 14 %.

## Steps
1. Four times: device deviates for 5 min.

## Expected result
- Rewrite, rewrite, rewrite, give up.

## Why it matters
No endless fight with a thermostat that regulates on its own.
