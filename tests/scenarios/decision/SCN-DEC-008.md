# SCN-DEC-008: Heating resumes only after the resume delay

**Spec:** RUL-014
**Test:** `tests/core/test_decisions.py::test_heating_resumes_only_after_the_resume_delay`

## Initial state
A room whose window was open (reason `window_open`); all contacts closed at 06:05.

## Steps
1. 9 s later; at the same moment the window opens again for a moment (switching to tilted).
2. 10 s after closing.
3. A window opens in a room with a close delay of 0 s.

## Expected result
- After 9 s still `window_open`, also when the contact opens again.
- After 10 s: back to `setpoint`.
- With 0 s: `window_open` at once.

## Why it matters
Switching from fully open to tilted must not start the radiator for a moment.
