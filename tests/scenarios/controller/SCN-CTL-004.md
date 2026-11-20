# SCN-CTL-004: The boiler profile reacts faster

**Spec:** CTL-011, CTL-013
**Test:** `tests/core/test_controller_simulation.py::test_boiler_profile_reacts_faster`

## Initial state
Room as SCN-CTL-001 with 60 °C flow and the boiler profile (0 %, 0.2 K, 30 %/30 min).

## Steps
1. Run 4 simulated days.

## Expected result
- Within ±0.3 K after ≤ 4 h, overshoot ≤ 0.4 K.

## Why it matters
Profiles really change the behaviour, as described on the house device.
