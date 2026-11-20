# SCN-CTL-014: A room above its target never gets more heat

**Spec:** CTL-043
**Test:** `tests/core/test_controller.py::test_room_above_target_never_gets_more_heat`

## Initial state
Target 20 °C, room 20.3 °C (inside the 0.5 K dead band), heat-pump profile with 40 % minimum opening, plan at 40 %.

## Steps
1. 15 minutes later the feed-forward rises to 54 % (e.g. falling flow temperature).

## Expected result
- The output stays at 40 %, limit `hold_when_warm`.

## Why it matters
Field finding: the guest bathroom was 0.3 K too warm while the plan climbed from 30 to 54 %.
