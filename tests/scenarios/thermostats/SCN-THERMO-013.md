# SCN-THERMO-013: The return sensor sets the measured spread

**Spec:** MDL-019
**Test:** `tests/ha/test_thermostats.py::test_return_sensor_sets_the_spread`

## Initial state
House with flow 40 °C and return 33 °C sensors; a room with a 1500 W radiator.

## Steps
1. Assign the thermostat.

## Expected result
- The planned valve position shows `return_temperature_used: 33.0` and `spread_used: 7.0`.

## Why it matters
Users see which spread the feed-forward is based on.
