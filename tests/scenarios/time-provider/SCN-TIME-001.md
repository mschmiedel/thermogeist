# SCN-TIME-001: Simulated time advances wall clock and monotonic clock together

**Spec:** TST-001, TST-002
**Test:** `tests/core/test_time_provider.py::test_advance_moves_both_clocks`

## Initial state
A `FakeTimeProvider` starts at 2026-11-20 06:00 UTC.

## Steps
1. Advance by 90 minutes.
2. Advance by 2 days.

## Expected result
- `now()` is 2026-11-22 07:30 UTC.
- `monotonic()` has grown by exactly 2 days + 90 minutes in seconds.

## Why it matters
Learning and timeouts use both clocks. If they drifted apart in tests, simulated weeks would not
reflect real behaviour.
