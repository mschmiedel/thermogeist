# SCN-CTL-018: The feed-forward does not grow with a warm room

**Spec:** CTL-030
**Test:** `tests/ha/test_thermostats.py::test_feed_forward_ignores_a_warm_room`

## Initial state
A room with a Sonoff (2000 W), flow 40 °C, target 20 °C, room 19.5 °C. Observe mode.

## Steps
1. The room warms to 22 °C (sun).

## Expected result
- The feed-forward stays the same: it is computed at the 20 °C target, not at the room.

## Why it matters
With the room temperature, PyM in the sun looked like a radiator that can hardly give
anything, and the feed-forward asked for 100 % at 22.8 °C.
