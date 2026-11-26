# SCN-HEATER-009: A heater is added through the room dialog

**Spec:** ACT-060, ACT-067
**Test:** `tests/ha/test_heaters.py::test_heater_is_added_and_mixing_is_rejected`

## Initial state
A house with a living room without thermostats, and a kitchen with a thermostat.

## Steps
1. In the living room choose "Add heater": switch, 2 stages, outputs "1300, 1700", without
   stage sensor and setter.
2. Add a stage sensor and save.
3. In the kitchen choose "Add heater".

## Expected result
1. Rejected at the stage sensor with `heater_needs_stage_entity`.
2. Saved; the room shows the heater sensor and the planned heat share.
3. The kitchen aborts with `room_has_thermostats`: a room has either thermostats or heaters.

## Why it matters
The heater is set up like a thermostat, and the dialog explains what is missing instead of
saving something that cannot work.
