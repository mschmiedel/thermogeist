# SCN-SHARE-004: Estimates above 100 % are scaled down and flagged

**Spec:** MDL-034
**Test:** `tests/core/test_estimation.py::test_estimates_above_available_are_scaled`

## Initial state
House with 50 m² living area (too small). Typical rooms of 40 m² and 30 m².

## Steps
1. Calculate the shares.

## Expected result
- Shares 57.14 % and 42.86 % (together 100 %).
- `scaled_down` is true, not assigned 0 %.

## Why it matters
Inconsistent inputs never produce more than 100 % of the heat load; the user sees that something does not add up.
