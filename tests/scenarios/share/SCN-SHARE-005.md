# SCN-SHARE-005: Known shares may not exceed 100 % together

**Spec:** MDL-021
**Test:** `tests/core/test_estimation.py::test_known_shares_exceeding_total_are_detected`

## Initial state
House with 10 % outside Thermogeist.

## Steps
1. Rooms with known shares 60 % and 35 %.
2. Rooms with known shares 55 % and 35 %.

## Expected result
- 1: exceeds (105 %).
- 2: does not exceed (exactly 100 %).

## Why it matters
The room dialog can reject impossible numbers right away.
