# SCN-ACT-004: Unknown thermostats fall back to the setpoint-based kind

**Spec:** ACT-020, ACT-031
**Test:** `tests/core/test_actuator.py::test_unknown_device_falls_back_to_setpoint_kind`

## Initial state
A device with only a climate entity and no matching profile.

## Steps
1. Resolve roles without profile.

## Expected result
- Only the climate role.
- Kind: setpoint-based.

## Why it matters
Every thermostat can be used; known ones just get more features.
