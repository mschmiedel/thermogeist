# SCN-THERMO-003: A thermostat needs a room

**Spec:** HAI-006
**Test:** `tests/ha/test_thermostats.py::test_thermostat_needs_a_room`

## Initial state
A house without rooms.

## Steps
1. Start "Add thermostat".

## Expected result
- The dialog ends with "Add a room first".

## Why it matters
No dead ends: the message says what to do.
