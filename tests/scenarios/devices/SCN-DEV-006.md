# SCN-DEV-006: A proportional thermostat leaves a gap when the radiator is tight

**Spec:** TST-012, ACT-056
**Test:** `tests/core/test_device_models.py::test_shc_leaves_a_gap_when_the_radiator_is_tight`

## Initial state
As SCN-DEV-005, but with a radiator that needs about 85 % to hold the room.

## Steps
1. Run three simulated days.

## Expected result
- Day 3 settles at least 0.8 K below the target, with the valve not fully open.

## Why it matters
Documents a device limit found with the model: without an integral part the device stops at a lasting gap, and sending the room target cannot close it. A setpoint correction for a lasting gap (ACT-056) is planned.
