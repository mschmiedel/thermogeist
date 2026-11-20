# SCN-TIME-002: Time never moves backwards

**Spec:** TST-003
**Test:** `tests/core/test_time_provider.py::test_negative_advance_is_rejected`

## Initial state
A `FakeTimeProvider` starts at 2026-11-20 06:00 UTC.

## Steps
1. Try to advance by −1 second.

## Expected result
- A `ValueError` is raised.
- `now()` and `monotonic()` are unchanged.

## Why it matters
Debouncing, overrides and learning windows assume time only moves forward. A test that moved
time backwards would test a situation that cannot happen.
