# SCN-SETPOINT-004: Setpoint writes are bundled, urgent ones go out at once

**Spec:** ACT-053
**Test:** `tests/core/test_setpoint.py::test_setpoint_writes_are_bundled`

## Initial state
20 °C was written at 06:00.

## Steps
1. Same value after 1 h; 20.5 °C after 9 min and after 10 min; 5 °C (window) after 30 s.

## Expected result
- First write always; no write for the same value; 20.5 °C only after 10 min; 5 °C at once.

## Why it matters
Every setpoint change is a radio message and may move the motor; windows still react at once.
