# SCN-CTL-016: The controller state survives a restart, but not a long outage

**Spec:** CTL-040, CTL-044
**Test:** `tests/core/test_controller.py::test_state_survives_a_restart_but_not_a_long_outage`

## Initial state
A controller with an integral of −7.5 % and a relaxed minimum opening, saved at 06:00.

## Steps
1. Restore it 5 minutes later.
2. Restore it 25 hours later.

## Expected result
- After 5 minutes: integral −7.5 % and the relaxed state are back; the last output is not
  restored (the valve's reported position seeds it).
- After 25 hours: nothing is restored.

## Why it matters
An update or restart no longer throws away hours of slow correction.
