# SCN-CALIB-004: Values for a thermostat without profile are set in the dialog

**Spec:** DIA-024
**Test:** `tests/ha/test_calibration.py::test_values_can_be_set_for_a_device_without_profile`

## Initial state
A thermostat Thermogeist has no profile for, with a calibration entity `sensor.old_trv_calibration`.

## Steps
1. In *More*, enter `Error` as values for "not calibrated" without choosing the calibration status.
2. Choose the calibration status and enter `error, lost`.
3. The entity shows `error` for 11 minutes.

## Expected result
- 1. is rejected: the values need the calibration status entity.
- 2. is saved; nothing is pre-filled for this device.
- 3. raises the repair issue *… is not calibrated* (values compared without case).

## Why it matters
Calibration loss is not limited to the models Thermogeist knows.
