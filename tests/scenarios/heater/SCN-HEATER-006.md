# SCN-HEATER-006: A heater that is on but does not run is reported

**Spec:** ACT-064
**Test:** `tests/core/test_heater.py::test_fault_when_switched_on_but_not_running`

## Initial state
A heater with a stage sensor, switched on at 08:00.

## Steps
1. At 08:02 the stage sensor still reports 0 (since 07:30, while the switch was off).
2. At 08:03 it still reports 0.
3. At 08:10 the switch is off again, the sensor reports 0.
4. At 08:20 the sensor reports stage 1.
5. At 09:00 the stage is changed by hand on the device: the sensor reports 0 from 09:00:00 to
   09:00:09, the switch has been on since 08:00.

## Expected result
- 08:02: no problem yet (start-up; the 3 minutes count from switching on).
- 08:03: problem.
- 08:10: the problem stays (nothing ran since).
- 08:20: cleared.
- 09:00:09: no problem – 0 for a few seconds is no fault.

## Why it matters
A tripped fuse or a broken fan otherwise goes unnoticed while Thermogeist counts heat that never
reaches the room; changing the stage by hand must not raise a false alarm.
