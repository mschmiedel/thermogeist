# SCN-CTL-023: A window does not lift a room that is too warm

**Spec:** RUL-010, CTL-043
**Test:** `tests/core/test_controller.py::test_window_does_not_lift_a_warm_room`

## Initial state
Heat-pump profile, controller at 60 %. The room becomes 0.6 K too warm while the feed-forward
rises to 90 %, so the plan is held at 60 %.

## Steps
1. Window open, then closed again while the room is still too warm.
2. Window open again, then closed while the room is 0.5 K too cold.

## Expected result
- 1: back to 60 % at once, limit `hold_when_warm` – not to the 88 % the calculation gives.
- 2: straight to the computed position (above 90 %), no slow ramp.

## Why it matters
Field finding: a window opened for 20 seconds in a room 0.6 K too warm moved the plan from 61 to
90 %. The thermostat then opens wide as soon as the room cools a little, and the room overheats.
