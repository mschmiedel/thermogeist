# SCN-THERMO-009: An implausible role is rejected in the dialog

**Spec:** ACT-035
**Test:** `tests/ha/test_thermostats.py::test_implausible_role_is_rejected`

## Initial state
A thermostat device with a temperature sensor.

## Steps
1. Choose the temperature sensor as "setpoint source".

## Expected result
- The dialog stays open with an explanation at that field.

## Why it matters
This is exactly the mix-up that happened with the Bosch Smart Home thermostat in the living test.
