# SCN-HEATER-002: Without a stage setter, the heater runs between off and its own stage

**Spec:** ACT-063, ACT-067
**Test:** `tests/core/test_heater.py::test_without_setter_heater_runs_between_off_and_its_stage`

## Initial state
The same two-stage heater (1300 W / 1700 W, 0 W while off), but without stage setter; the
stage sensor last saw stage 1.

## Steps
1. Plan 50 % (850 W) of the top stage.
2. Plan 100 %.

## Expected result
- 50 %: off and stage 1, share 850 / 1300 ≈ 65 %.
- 100 %: still off and stage 1, all the time on stage 1 – more is not possible.

## Why it matters
Most heaters cannot be told their stage. Thermogeist then works with the stage the device
chose and still meets the demand on average.
