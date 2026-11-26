# SCN-HEATER-001: Heat is placed between two neighbouring stages

**Spec:** ACT-063, ACT-067
**Test:** `tests/core/test_heater.py::test_heat_is_placed_between_neighbouring_stages`

## Initial state
A two-stage heater with a stage setter: stage 1 gives 1300 W, stage 2 gives 1700 W, 40 W
while off.

## Steps
1. Plan 0 %, 50 %, 85 % and 100 % of the top stage.

## Expected result
- 0 %: off and stage 1, no time on stage 1.
- 50 % (850 W): between off and stage 1, share (850 − 40) / (1300 − 40) ≈ 64 %.
- 85 % (1445 W): between stage 1 and 2, share (1445 − 1300) / 400 ≈ 36 %.
- 100 %: stage 1 and 2, all the time on stage 2.

## Why it matters
A heater with a selectable stage runs on the lowest stages that cover the demand, which is
quieter and calmer than switching the top stage on and off.
