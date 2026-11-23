# SCN-CTL-025: A room clearly below its target never gets less heat

**Spec:** CTL-046
**Test:** `tests/core/test_controller.py::test_room_below_target_never_gets_less_heat`

## Initial state
Heat-pump settings (dead band 0.5 K), target 20.0 °C, room 19.2 °C, feed-forward 70 %.

## Steps
1. After 15 minutes the feed-forward falls to 48 % (flow and outdoor temperature rose); the room is still 19.2 °C.
2. After another 15 minutes the room is 19.7 °C, inside the dead band below the target.

## Expected result
- 1. the output stays where it was, limit `hold_when_cold`.
- 2. the output may go down, so the room does not overshoot.

## Why it matters
Field finding: the bathroom was 0.8 K too cold at noon, and the plan fell from 100 to 89 % because the calculation expected less demand – just when the room could have caught up.
