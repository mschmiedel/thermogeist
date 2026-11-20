# SCN-CONTROL-003: Switching control off gives the device back

**Spec:** ACT-008, ACT-042
**Test:** `tests/ha/test_control.py::test_switching_off_restores_the_device`

## Initial state
Controlled Bosch, originally `operating_mode` schedule and valve 39 %.

## Steps
1. Switch control off.

## Expected result
- `operating_mode` back to schedule, valve back to 39 %.

## Why it matters
Trying Thermogeist is always reversible.
