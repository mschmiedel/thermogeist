# SCN-CTL-007: Feed-forward converts watts into a valve position

**Spec:** CTL-030, CTL-036, MDL-012
**Test:** `tests/core/test_controller.py::test_feed_forward_inverts_typical_valve_characteristic`

## Initial state
Radiator 2000 W, flow 40 °C, room 20 °C, demand 400 W.

## Steps
1. Compute available output and feed-forward.
2. Flow below room temperature.
3. Missing data.

## Expected result
- 1: available = 2000 × (17.5/49.8)^1.3 W; valve = 10 % + 90 % × (400/available)².
- 2: 100 %.
- 3: no feed-forward.

## Why it matters
The model gives a sensible starting point instead of waiting for the room to get cold.
