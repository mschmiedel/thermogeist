# SCN-CTL-011: The start value never adds to a feed-forward

**Spec:** CTL-032
**Test:** `tests/core/test_controller.py::test_start_value_is_removed_when_feed_forward_arrives`

## Initial state
Controller without feed-forward at the first step (e.g. flow sensor not yet available after a restart).

## Steps
1. Step without feed-forward.
2. Feed-forward 36.9 % arrives.
3. Feed-forward lost again.

## Expected result
- 1: integral 30 % (start value).
- 2: integral 0 % – the start value is removed.
- 3: integral 30 % again.

## Why it matters
Seen in the field: the start value stayed and counted twice, the guest bathroom would have been driven to 67 % instead of 37 %.
