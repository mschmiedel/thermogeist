# SCN-CONTROL-015: The Sonoff's resting position follows a relaxed minimum

**Spec:** ACT-102, CTL-037, CTL-043
**Test:** `tests/ha/test_control.py::test_sonoff_rest_position_follows_relaxed_minimum`

## Initial state
A controlled Sonoff TRVZB in a heat-pump house (minimum opening 40 %, closing degree 60 %),
target 20 °C.

## Steps
1. The room warms to 23 °C and stays there for hours.
2. The room cools back below its target (19.8 °C) for four hours.

## Expected result
1. Once the plan goes below the minimum, the closing degree follows it (above 60 %).
2. The plan climbs back (rate-limited); the closing degree follows and is 60 % again once the
   plan has reached the minimum opening.

## Why it matters
The Sonoff rests on its closing position while the room is above its setpoint; with a fixed
closing position a room warmed by sun never got less than the minimum.
