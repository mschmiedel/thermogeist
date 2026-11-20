# SCN-CTL-012: A slow ramp is written in a few bigger steps

**Spec:** ACT-046, CTL-033
**Test:** `tests/core/test_actuation.py::test_slow_ramp_is_written_in_few_bigger_steps`

## Initial state
Heat-pump profile (10 %/30 min). The plan jumps from 30 % to 67 % (as seen in the field).

## Steps
1. Run 150 minutes and count controller changes and writes to the device.

## Expected result
- The controller moves in 1 % steps (≥ 30 changes).
- At most 12 writes reach the device; the final 67 % is reached.

## Why it matters
Every write moves a battery-powered motor. Field test: 1 % steps every 3 minutes were too many.
