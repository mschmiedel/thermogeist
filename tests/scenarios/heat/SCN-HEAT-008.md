# SCN-HEAT-008: A room estimate needs every radiator

**Spec:** MDL-013
**Test:** `tests/core/test_output.py::test_room_estimate_needs_every_radiator`

## Initial state
A room with two radiators, flow 45 °C, room 20 °C, no measured spread.

## Steps
1. Both have a rated output and a valve position.
2. The second has no valve position.
3. The flow temperature is missing.

## Expected result
1. The output is the sum of both; the maximum is the sum of both fully open.
2. No output (`missing: valve_position`); the maximum is still shown.
3. Neither output nor maximum (`missing: flow_temperature`).

## Why it matters
Half a room's radiators summed up would look like a precise but wrong number.
