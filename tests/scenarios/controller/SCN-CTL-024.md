# SCN-CTL-024: The minimum opening returns only at the target

**Spec:** CTL-037, CTL-043
**Test:** `tests/core/test_controller.py::test_minimum_opening_returns_at_the_target`

## Initial state
Heat-pump settings (minimum opening 40 %, dead band 0.5 K), target 20.0 °C, feed-forward 30 %.

## Steps
1. The room is 21.2 °C: more than 0.5 K above the dead band.
2. It cools to 20.8, 20.3 and 20.1 °C, 15 minutes apart.
3. It reaches 20.0 °C.

## Expected result
- 1. relaxes the minimum opening (`min_opening_relaxed`).
- 2. stays below the minimum opening: inside the dead band the valve may be regulated below it while the room is still above its target.
- 3. the minimum opening applies again (`min_opening`), at once: no slow ramp up to it.

## Why it matters
A bedroom warmed by sleeping people would otherwise swing between the end of the dead band and the relax limit, always too warm; and the minimum opening would never come back while the room is held above its target.
