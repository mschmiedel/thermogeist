# SCN-SUP-003: Old rewrites age out after an hour

**Spec:** ACT-043
**Test:** `tests/core/test_supervision.py::test_rewrites_age_out_after_an_hour`

## Initial state
Three rewrites happened.

## Steps
1. One hour later the device deviates again.

## Expected result
- Rewrite again (not give up).

## Why it matters
A rare glitch does not add up over days.
