# SCN-DEC-006: A window counts as open after 30 seconds

**Spec:** RUL-010
**Test:** `tests/core/test_decisions.py::test_window_counts_after_30_seconds`

## Initial state
Room with setpoint 21 °C, sensor fresh. A window opens.

## Steps
1. Decide after 29 s.
2. Decide after 30 s.
3. Same with central mode stop.

## Expected result
- 1: `setpoint`.
- 2: `window_open`, target 7 °C.
- 3: `central_stop` (central mode has precedence).

## Why it matters
Short airing does not disturb control; a real open window stops heating.
