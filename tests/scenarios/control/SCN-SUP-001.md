# SCN-SUP-001: Small or short deviations of the valve are tolerated

**Spec:** ACT-043
**Test:** `tests/core/test_supervision.py::test_small_or_short_deviations_are_tolerated`

## Initial state
40 % written.

## Steps
1. Device reports 44 %.
2. Device reports 14 % for 4:59 min.
3. Still 14 % after 5:00 min.

## Expected result
- 1, 2: OK.
- 3: write again.

## Why it matters
Devices round and report late; Thermogeist does not react to that.
