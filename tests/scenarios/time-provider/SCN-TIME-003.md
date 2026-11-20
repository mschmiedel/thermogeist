# SCN-TIME-003: Timestamps without timezone are rejected, others are normalised to UTC

**Spec:** TST-001, TST-003
**Test:** `tests/core/test_time_provider.py::test_start_time_must_be_timezone_aware`

## Initial state
None.

## Steps
1. Create a `FakeTimeProvider` with a timestamp that has no timezone.
2. Create a `FakeTimeProvider` with 2026-11-20 07:00 in UTC+1.

## Expected result
- Step 1 raises a `ValueError`.
- Step 2 reports `now()` as 2026-11-20 06:00 UTC.

## Why it matters
Schedules and daylight-saving changes are a classic source of off-by-one-hour bugs. Working in
UTC internally avoids them.
