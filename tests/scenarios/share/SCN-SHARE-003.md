# SCN-SHARE-003: Without living area, estimated rooms share what is left

**Spec:** MDL-035
**Test:** `tests/core/test_estimation.py::test_without_living_area_estimated_rooms_share_the_rest`

## Initial state
House without living area, 10 % outside Thermogeist. One room with known share 30 %, two typical rooms of 20 m² and 10 m².

## Steps
1. Calculate the shares.

## Expected result
- Known room 30 %, estimated rooms 40 % and 20 %.
- Not assigned 0 %.

## Why it matters
The fallback still produces sensible numbers when the living area is unknown.
