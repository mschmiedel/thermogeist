# SCN-DEC-002: Central stop and frost protection override the setpoint

**Spec:** RUL-003, RUL-004
**Test:** `tests/core/test_decisions.py::test_central_mode_overrides_setpoint`

## Initial state
Sensor fresh, setpoint 21 °C.

## Steps
1. Central mode stop.
2. Central mode frost protection.

## Expected result
- 1: code `central_stop`, no target.
- 2: code `frost_protection`, target 7 °C.

## Why it matters
One switch for the whole house, and every room says why it does not heat.
