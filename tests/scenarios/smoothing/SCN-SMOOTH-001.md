# SCN-SMOOTH-001: The flow temperature is averaged and checked

**Spec:** CTL-038, CTL-039
**Test:** `tests/core/test_smoothing.py::test_flow_is_averaged_over_30_minutes_and_checked`

## Initial state
A flow sensor toggling 32.5 / 32.25 °C, then one drop to 28 °C.

## Steps
1. Average after 20 minutes.
2. Average after 60 minutes without new values.
3. Plausibility of 29, 85, −127 °C.

## Expected result
- 1: mean of all 21 samples.
- 2: no value (window empty).
- 3: only 29 °C is plausible.

## Why it matters
Sensor noise and single dips no longer push the feed-forward around.
