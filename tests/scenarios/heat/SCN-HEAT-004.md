# SCN-HEAT-004: A measured spread replaces the assumed 5 K

**Spec:** MDL-019
**Test:** `tests/core/test_setpoint.py::test_measured_spread_replaces_the_assumption`

## Initial state
Flow 40 °C, room 20 °C, radiator 1000 W rated.

## Steps
1. Compute the spread for return 33 °C, 39.8 °C, 20 °C and without return.
2. Compare radiator output and feed-forward for 5 K and 8 K spread.

## Expected result
- 7 K; limited to 1 K and 10 K; None without return.
- 5 K equals the assumption; 8 K gives less output and a larger feed-forward opening.

## Why it matters
With a large spread the radiators are cooler than assumed; the valves must open further.
