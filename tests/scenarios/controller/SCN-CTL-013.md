# SCN-CTL-013: When a position is worth writing

**Spec:** ACT-046
**Test:** `tests/core/test_actuation.py::test_urgent_changes_are_written_at_once`

## Initial state
Last write 45 % at minute 0.

## Steps
1. Urgent 0 % after 1 min.
2. 47 % after 1 min.
3. 48 % after 10 min.
4. 47 % after 29 and 30 min.

## Expected result
- 1: written (window, stop, safety are urgent).
- 2: not written.
- 3: written (≥ 3 % and ≥ 10 min).
- 4: not yet, then written (small rest after 30 min).

## Why it matters
Big steps go out promptly, small ones are bundled, urgent ones never wait.
