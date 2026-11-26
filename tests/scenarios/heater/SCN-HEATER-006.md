# SCN-HEATER-006: A heater that is on but does not run is reported

**Spec:** ACT-064
**Test:** `tests/core/test_heater.py::test_fault_when_switched_on_but_not_running`

## Initial state
A heater with a stage sensor, switched on at 08:00.

## Steps
1. At 08:02 the stage sensor still reports 0.
2. At 08:03 it still reports 0.
3. At 08:10 the switch is off again, the sensor reports 0.
4. At 08:20 the sensor reports stage 1.

## Expected result
- 08:02: no problem yet (start-up).
- 08:03: problem.
- 08:10: the problem stays (nothing ran since).
- 08:20: cleared.

## Why it matters
A tripped fuse or a broken fan otherwise goes unnoticed while Thermogeist counts heat that never
reaches the room.
