# SCN-CALIB-001: The profile says which values mean "not calibrated"

**Spec:** DIA-024
**Test:** `tests/core/test_calibration.py::test_profile_values_mean_not_calibrated`

## Initial state
The values from the profiles: Sonoff TRVZB `closing_steps` 0; Bosch BTH-RA `valve_adapt_status` none, ready_to_calibrate, error.

## Steps
1. Compare reported values with them.

## Expected result
- `0` and `0.0` mean not calibrated, `337` does not.
- `ready_to_calibrate` means not calibrated, `success` does not.
- No value means: unknown.

## Why it matters
Device quirks live in the profile; the code only compares.
