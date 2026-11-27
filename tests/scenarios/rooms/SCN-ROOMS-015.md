# SCN-ROOMS-015: Closing the dialog keeps the new room and its finished thermostats

**Spec:** HAI-021
**Test:** `tests/ha/test_rooms.py::test_cancelled_dialog_keeps_the_new_room`

## Initial state
A house; a Sonoff TRVZB that Thermogeist knows by its profile.

## Steps
1. Add a room (basics, size and position).
2. Add the Sonoff as a thermostat and confirm its roles.
3. Choose *Add a thermostat* again and close the dialog in the device step, for example because
   a value is not at hand.

## Expected result
- The room exists with its name and the one finished thermostat.
- Its planned valve position exists; only the device of step 3 is lost.

## Why it matters
Home Assistant dialogs have no *Back*, and closing one ends the whole dialog. Before, a room was
saved only at *Done*, so a missing value for the second device threw away the room and every
device already entered.
