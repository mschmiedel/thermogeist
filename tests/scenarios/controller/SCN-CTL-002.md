# SCN-CTL-002: Without heat load and radiator data the room still reaches its target

**Spec:** CTL-032, MDL-020
**Test:** `tests/core/test_controller_simulation.py::test_feedback_only_still_reaches_target`

## Initial state
Same room as SCN-CTL-001, but the controller knows neither heat loss nor radiator output.

## Steps
1. Run 4 simulated days.

## Expected result
- Overshoot ≤ 0.3 K, within ±0.3 K after ≤ 36 h.
- Day 3: ≤ 10 valve moves.

## Why it matters
Thermogeist works for beginners too – it only takes longer.
