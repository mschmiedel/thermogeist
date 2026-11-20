# SCN-ACT-006: Profiles say which devices need a confirmed valve position

**Spec:** ACT-047
**Test:** `tests/core/test_actuator.py::test_bosch_profile_asks_for_valve_confirmation`

## Initial state
The shipped profiles.

## Steps
1. Read the refresh interval of Bosch and Sonoff.

## Expected result
- Bosch: 10 minutes. Sonoff: none.

## Why it matters
Only devices that need it get the extra messages.
