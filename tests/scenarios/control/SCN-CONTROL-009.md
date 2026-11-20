# SCN-CONTROL-009: The valve confirmation is set per thermostat

**Spec:** ACT-047, ACT-048
**Test:** `tests/ha/test_control.py::test_confirmation_interval_is_configurable`

## Initial state
A Bosch BTH-RA being assigned.

## Steps
1. The dialog suggests 10 minutes from the profile; the user clears it.
2. Control runs 30 minutes with a steady plan.

## Expected result
- No confirmations, one write.
- The thermostat shows `valve_refresh_minutes: null`, `last_write`, `last_confirmation: null`, `rewrites_last_hour: 0`.

## Why it matters
Only devices that need it get confirmations, and users see what Thermogeist did.
