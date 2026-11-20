# SCN-SHARE-006: A bathroom designed for 24 °C gets a larger share

**Spec:** MDL-039
**Test:** `tests/core/test_estimation.py::test_bathroom_design_temperature_raises_share`

## Initial state
House 160 m², design outdoor temperature −10.5 °C. Bathroom 8 m², typical otherwise, design indoor temperature 24 °C.

## Steps
1. Calculate the share.
2. Calculate again for a house without design outdoor temperature.

## Expected result
- 1: 5 % × 34.5 K / 30.5 K = 5.66 %.
- 2: 5 % (without the design outdoor temperature the temperature factor is not applied).

## Why it matters
Bathrooms are planned warmer; the estimate follows the heat load calculation.
