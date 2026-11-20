# SCN-ACT-005: Role assignments are checked for plausibility

**Spec:** ACT-035
**Test:** `tests/core/test_actuator.py::test_role_assignments_are_checked_for_plausibility`

## Initial state
A temperature sensor (24.4 °C), a valve position (24 %), a setpoint source (`manual`).

## Steps
1. Check each against the setpoint source, valve position, external temperature and child lock roles.

## Expected result
- Temperature as setpoint source or valve position: rejected.
- Percentage as external temperature: rejected.
- Matching entities and roles without rules (child lock): accepted.

## Why it matters
Since any entity can be chosen, wrong picks must be caught before they matter in control mode.
