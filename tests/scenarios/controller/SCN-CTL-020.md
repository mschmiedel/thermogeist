# SCN-CTL-020: A window open since start-up does not slow the return

**Spec:** RUL-010
**Test:** `tests/core/test_controller.py::test_window_open_from_the_start_returns_at_once`

## Initial state
Heat-pump profile (max. 10 % per 30 minutes). After a restart the controller starts from the
reported valve position, 0 %, because the window has been open since before the restart.

## Steps
1. Window open for 30 minutes.
2. Window closed; the controller computes 69 % (feed-forward 60 % + proportional).
3. One minute later.

## Expected result
- 1: 0 %, limit `window`.
- 2: 69 % at once, no `rate_limit`.
- 3: the rate limit applies again from 69 %.

## Why it matters
The dining room's contacts were detached across a restart; after attaching them the plan
crept up from the 0 % it had started from, by about 1 % every three minutes.
