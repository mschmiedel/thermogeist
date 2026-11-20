# SCN-CONTROL-006: An open window closes the valve, closing reopens it

**Spec:** RUL-010
**Test:** `tests/ha/test_control.py::test_window_closes_valve_and_reopens`

## Initial state
Controlled room with a window contact.

## Steps
1. Window open for 31 s.
2. Window closed.

## Expected result
- 1: reason `window_open`, valve written 0 %.
- 2: reason `setpoint`, valve back to the previous position.

## Why it matters
Airing is handled without wasting heat and without slow recovery.
