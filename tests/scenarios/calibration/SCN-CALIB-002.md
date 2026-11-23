# SCN-CALIB-002: Only a lasting "not calibrated" is reported

**Spec:** DIA-024
**Test:** `tests/core/test_calibration.py::test_only_a_lasting_state_counts`

## Initial state
A thermostat whose profile knows its calibration status.

## Steps
1. It reports "not calibrated" for a minute (a calibration passes through these values), then calibrated.
2. It reports "not calibrated" again, with a gap without any value.
3. It stays so for 10 minutes (`CALIBRATION_LOST_AFTER`).
4. Hours later it reports calibrated.

## Expected result
- 1. and 2. raise nothing; a missing value neither raises nor clears.
- 3. marks it lost once.
- 4. clears it once.

## Why it matters
A normal calibration after mounting must not raise a repair issue.
