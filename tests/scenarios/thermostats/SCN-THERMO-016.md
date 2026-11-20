# SCN-THERMO-016: Existing thermostats move into their room on update

**Spec:** HAI-007
**Test:** `tests/ha/test_restart_and_migration.py::test_thermostat_subentries_move_into_their_room`

## Initial state
A house stored in the old format: one room and one thermostat sub-entry "Old TRV" with a rated
output of 700 W, and its *Kind* entity in the registry.

## Steps
1. Home Assistant loads the house.

## Expected result
- Only the room sub-entry remains; the room lists the thermostat under its old id with name,
  rated output and roles.
- The *Kind* entity keeps its id and works.

## Why it matters
Updating does not lose thermostats, settings or history.
