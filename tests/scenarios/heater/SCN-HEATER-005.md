# SCN-HEATER-005: Output on the heating circuit follows the heater's own exponent

**Spec:** ACT-061, ACT-062, ACT-063
**Test:** `tests/core/test_heater.py::test_heating_circuit_output_and_linear_feed_forward`

## Initial state
A fan convector on the heating circuit, 1700 W at 75/65/20 °C on its top stage, exponent 1.0;
an infrared panel (direct) with 600 W. Flow 37.5 °C, room 20 °C, spread 5 K.

## Steps
1. Ask the available output of the top stages.
2. Ask the feed-forward for a net demand of 400 W.
3. Ask again without flow temperature.

## Expected result
- Fan convector: 1700 · (15 / 49.8)^1.0 ≈ 512 W; infrared: 600 W regardless of the flow.
- Feed-forward: 400 / (512 + 600) ≈ 36 %, linear.
- Without flow: the convector is unknown, so the feed-forward is unknown; the panel alone
  still has its 600 W.

## Why it matters
A fan convector gives much more heat at a low flow temperature than a radiator with the same
rated output, and electricity does not depend on the flow at all.
