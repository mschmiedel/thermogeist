# SCN-THERMO-015: Removing a thermostat from its room

**Spec:** HAI-007, ACT-008
**Test:** `tests/ha/test_thermostats.py::test_remove_thermostat_from_room`

## Initial state
A room with one Sonoff TRVZB.

## Steps
1. Gear icon → *Remove thermostat* → choose the thermostat.

## Expected result
- The room no longer lists it; its entities (e.g. *Kind*) are gone.

## Why it matters
Moving a thermostat to another room is "remove here, add there".
