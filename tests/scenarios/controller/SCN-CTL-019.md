# SCN-CTL-019: A lasting overshoot lowers the correction

**Spec:** CTL-032
**Test:** `tests/core/test_controller.py::test_lasting_overshoot_lowers_the_correction`

## Initial state
Heat-pump settings, target 21.5 °C, feed-forward 100 % (the model overestimates the demand),
time constant 10 h.

## Steps
1. The room stays at 22.8 °C (1.3 K too warm, outside the ±1 K band) for two hours.
2. The room is 2 K below its target for two hours.

## Expected result
1. The correction (integral) falls below 0.
2. It does not rise: far below the target the proportional part works alone, so heating up
   does not wind the correction up.

## Why it matters
PyM stayed 1.3 K too warm for hours while the correction stood still and the plan waited at
74 %.
