# SCN-THERMO-004: Unknown thermostats work setpoint-based

**Spec:** ACT-020, ACT-031
**Test:** `tests/ha/test_thermostats.py::test_unknown_device_uses_setpoint_kind`

## Initial state
A device "Old TRV" by an unknown maker with only a climate entity.

## Steps
1. Assign it.

## Expected result
- No profile; only the climate role is pre-filled.
- Kind setpoint-based; the room's strategies show "setpoint".

## Why it matters
Every thermostat can be used, known ones just get more.
