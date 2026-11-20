# SCN-THERMO-011: A restart continues from the reported valve position

**Spec:** CTL-044
**Test:** `tests/ha/test_control.py::test_restart_starts_from_the_reported_valve`

## Initial state
A Bosch reporting 39 %.

## Steps
1. Reload the integration.

## Expected result
- The planned position starts at about 39 %.

## Why it matters
No jump after restarts or updates.
