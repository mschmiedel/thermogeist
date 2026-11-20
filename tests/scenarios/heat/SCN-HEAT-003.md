# SCN-HEAT-003: Design indoor temperature changes the heat loss, the setpoint the demand

**Spec:** MDL-039, MDL-011
**Test:** `tests/core/test_heat.py::test_design_indoor_temperature_changes_heat_loss_not_demand_target`

## Initial state
House 6.5 kW at −10.5 °C. Bathroom with 2 % share, designed for 24 °C.

## Steps
1. Calculate the heat loss coefficient.
2. Calculate the demand at setpoint 21 °C and 5 °C outdoors.

## Expected result
- 1: 130 W / 34.5 K = 3.77 W/K.
- 2: 3.77 W/K × 16 K = 60 W – based on 21 °C, not 24 °C.

## Why it matters
The design temperature is a planning value; how warm the room is heated is decided by the setpoint.
