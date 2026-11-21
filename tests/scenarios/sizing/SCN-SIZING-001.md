# SCN-SIZING-001: The load on the design day decides the radiator size

**Spec:** DIA-001 to DIA-004
**Test:** `tests/core/test_sizing.py::test_classification_thresholds`

## Initial state
Loads on the design day of 29.9 %, 30 %, 90 %, 95 %, 100 % and 100.1 % of the radiator output.

## Steps
1. Classify each load.

## Expected result
Heavily oversized below 30 %; right size from 30 % up to 90 %; tight up to 100 %; undersized
above 100 %.

## Why it matters
The borders are what the user sees on the sensor; they must be exactly as documented.
