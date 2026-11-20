# SCN-THERMO-014: The room's gear icon manages its thermostats

**Spec:** HAI-007
**Test:** `tests/ha/test_thermostats.py::test_room_menu_offers_thermostat_actions`

## Initial state
A house with one room and no thermostat.

## Steps
1. Open the room's gear icon.
2. Add a Sonoff TRVZB through *Add thermostat*; open the gear icon again.

## Expected result
- First: *Edit room* and *Add thermostat* only.
- Then also *Edit thermostat* and *Remove thermostat*.
- The house has only room sub-entries; no separate thermostat cards.

## Why it matters
Thermostats appear where they belong: inside their room.
