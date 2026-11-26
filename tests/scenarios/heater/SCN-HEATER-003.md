# SCN-HEATER-003: Minimum run time with carry-over

**Spec:** ACT-063
**Test:** `tests/core/test_heater.py::test_minimum_run_time_is_carried_over`

## Initial state
A cycler at 08:00, plan: off and stage 1, 15 % on stage 1 (3 of 20 minutes).

## Steps
1. Run four cycles of 20 minutes, asking every minute which stage to run.

## Expected result
- First cycle: 3 minutes are below the 5-minute minimum, so the heater stays off; the 3 minutes
  are carried over.
- Second cycle: 3 + 3 = 6 minutes on stage 1.
- Over the four cycles the heater ran 12 of 80 minutes (15 %).

## Why it matters
A small demand is still met on average, while the relay and fan never run for only a minute or
two.
