# SCN-DEC-001: Normally the room holds the user setpoint

**Spec:** ARC-003, RSN-002
**Test:** `tests/core/test_decisions.py::test_normal_operation_holds_setpoint`

## Initial state
Central mode auto, sensor reported 5 minutes ago, setpoint 21 °C.

## Steps
1. Decide.

## Expected result
- Code `setpoint`, target 21 °C, severity info.

## Why it matters
The everyday state is visible too: "holding the setpoint".
