# SCN-CTL-010: Window: valve closes at once and resumes where it was

**Spec:** RUL-010
**Test:** `tests/core/test_controller.py::test_window_closes_at_once_and_resumes_where_it_was`

## Initial state
Heat-pump profile, controller at 60 %.

## Steps
1. Window open.
2. Window closed 20 minutes later.

## Expected result
- 1: 0 % immediately (no rate limit), limit `window`.
- 2: back to 60 % immediately, no slow ramp.

## Why it matters
Airing costs no comfort afterwards: the room does not wait hours for the valve to reopen.
