# SCN-CTL-005: An oversized radiator may go below the minimum opening

**Spec:** CTL-037, CTL-020
**Test:** `tests/core/test_controller_simulation.py::test_oversized_radiator_relaxes_minimum_opening`

## Initial state
Simulated guest bathroom: 3 m², 4.3 W/K, 1000 W radiator. Outdoor 5 °C, flow 35 °C, heat-pump profile.

## Steps
1. Run 4 simulated days.

## Expected result
- Day 3 never above 21.1 °C (without the rule: 22.2 °C).
- The limit `min_opening_relaxed` appears, the valve goes below 40 %.

## Why it matters
Comfort beats the minimum opening. The valve cycles a few times a day, which is the honest consequence of an oversized radiator.
