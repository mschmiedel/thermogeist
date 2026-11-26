# SCN-HEATER-011: The heater shows its stage, heat output and problems

**Spec:** ACT-064, ACT-065, MDL-013
**Test:** `tests/ha/test_heaters.py::test_heater_sensor_output_and_fault`

## Initial state
A living room with a two-stage fan convector on the heating circuit (1300 / 1700 W, exponent
1.0), its switch on, a stage sensor, flow 40 °C.

## Steps
1. The stage sensor reports 2.
2. The stage sensor reports 0 for 3 minutes.
3. It reports 1 again.

## Expected result
1. The heater sensor shows 2 with the available output of stage 2; the room's estimated output
   equals it.
2. The problem binary sensor turns on, a repair issue appears, the estimated output is 0 W.
3. The problem is cleared and the issue removed.

## Why it matters
Users see what the heater does and are told when it does not run although it should.
