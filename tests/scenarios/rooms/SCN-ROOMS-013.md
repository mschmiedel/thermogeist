# SCN-ROOMS-013: Estimated radiator output next to the heat demand

**Spec:** MDL-013
**Test:** `tests/ha/test_estimated_output.py::test_estimated_output_from_reported_valve`

## Initial state
A room with a Bosch thermostat (700 W rated), flow 40 °C, room 19.5 °C, the thermostat reports
its valve at 39 %. Observe mode.

## Steps
1. Read the sensor *Estimated radiator output*.
2. Remove the reported valve position.

## Expected result
1. About 106 W; `max_output_w` about 186 W; the radiator shows valve 39 % `reported`.
2. Unknown, with `missing: valve_position` (in observe mode the plan is not what the valve does).

## Why it matters
Users compare what the radiator gives with what the room needs.
