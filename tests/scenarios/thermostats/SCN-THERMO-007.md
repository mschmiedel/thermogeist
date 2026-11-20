# SCN-THERMO-007: Roles may come from another device

**Spec:** ACT-033
**Test:** `tests/ha/test_thermostats.py::test_roles_may_come_from_another_device`

## Initial state
Like the Bosch Smart Home integration: the climate entity sits on a device "Room climate Roy", the valve position on a separate device "Roy TRV".

## Steps
1. Add thermostat with the climate device.
2. Choose the valve position sensor of the other device for "valve position (read)".

## Expected result
- The thermostat is created.
- The actual valve position shows 24 %; kind setpoint-based (no valve can be written).

## Why it matters
Integrations differ in how they split entities across devices; Thermogeist must not depend on that.
