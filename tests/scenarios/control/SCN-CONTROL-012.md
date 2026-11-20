# SCN-CONTROL-012: A Bosch BTH-RA can be controlled by setpoint

**Spec:** ACT-050, ACT-051, ACT-054
**Test:** `tests/ha/test_control.py::test_bosch_can_be_controlled_by_setpoint`

## Initial state
A Bosch BTH-RA with valve access, but the user chose the strategy *setpoint*. Room 19.5 °C,
target 20 °C, device setpoint 18 °C.

## Steps
1. Switch control on; wait for the start-up hold.

## Expected result
- Kind `setpoint`; no valve writes.
- The room temperature goes to `remote_temperature`, operating mode becomes `manual`.
- The device setpoint becomes the plain room target 20 °C (external input, no offset).

## Why it matters
Users who do not want valve control can let the device regulate on the right temperature.
