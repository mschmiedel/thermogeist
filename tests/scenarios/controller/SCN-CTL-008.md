# SCN-CTL-008: Small overshoot does not close the valve, but is removed slowly

**Spec:** CTL-031, CTL-032
**Test:** `tests/core/test_controller.py::test_dead_band_calms_proportional_part_only`

## Initial state
Target 20 °C, room 20.4 °C (inside the 0.5 K dead band), feed-forward 60 %, τ 10 h.

## Steps
1. Step.
2. Step one hour later.

## Expected result
- Proportional part 0, output 60 %.
- After the second step (one hour later) the integral has moved to −0.6 % for the next step.

## Why it matters
Sun through the window does not slam the valve shut; a lasting overshoot still fades.
