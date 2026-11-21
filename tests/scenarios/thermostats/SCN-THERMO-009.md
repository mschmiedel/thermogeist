# SCN-THERMO-009: An implausible role is rejected in the dialog

**Spec:** ACT-035
**Test:** `tests/ha/test_thermostats.py::test_implausible_role_is_rejected`

## Initial state
A thermostat device with a temperature sensor.

## Steps
1. Choose the temperature sensor as "valve position (read)".

## Expected result
- The dialog stays open with an explanation at that field.

## Why it matters
A temperature read as a valve position would make every valve comparison wrong.
