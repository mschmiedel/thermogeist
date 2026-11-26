# SCN-HEATER-004: New plans wait for the next cycle, a window switches off at once

**Spec:** ACT-063
**Test:** `tests/core/test_heater.py::test_new_plan_waits_for_next_cycle_and_interrupt_is_immediate`

## Initial state
A cycler at 08:00 with a plan of 50 % on stage 1.

## Steps
1. At 08:05 the plan changes to 100 %.
2. At 08:12 the window opens (interrupt).
3. At 08:13 the plan is 100 % again.

## Expected result
- 08:05: still the first cycle, stage 1 (from 08:00 to 08:10), then off at 08:10.
- After the interrupt a new cycle starts at 08:13 with stage 1 all the time.

## Why it matters
Relay and fan are not switched by every small change of the plan, but a window or central stop
acts at once.
