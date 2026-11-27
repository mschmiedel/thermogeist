# SCN-ROOMS-014: A new room offers to add its thermostats right away

**Spec:** HAI-021, HAI-020, HAI-016
**Test:** `tests/ha/test_rooms.py::test_new_room_offers_thermostats`

## Initial state
A house; a Sonoff TRVZB that Thermogeist knows by its profile.

## Steps
1. Add a room (basics, size and position).
2. At the question *Add a thermostat / Done* choose *Add a thermostat*, pick the Sonoff.
3. In the roles step keep the detected roles (pre-filled, as the frontend submits them) and
   confirm.
4. Choose *Done*.

## Expected result
- After step 1 the room is saved (without thermostats) and the question appears.
- In the roles step *How to control* is visible; the detected roles sit in a collapsed
  section; confirming without opening it keeps them.
- After step 3 the thermostat is saved with the room and the question appears again, now with
  one thermostat.
- Step 4 closes the dialog with "room saved"; there is one room with the thermostat and its
  planned valve position exists.

## Why it matters
Users found no obvious place to add the first thermostat after creating a room.
