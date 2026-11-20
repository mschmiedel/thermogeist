# SCN-HEAT-001: Heat loss and demand of a room

**Spec:** MDL-010, MDL-011
**Test:** `tests/core/test_heat.py::test_heat_loss_and_demand`

## Initial state
House 6.5 kW at −10.5 °C. Room share 12.5 %.

## Steps
1. Calculate the heat loss coefficient.
2. Demand at setpoint 21 °C and 5 °C outdoors.
3. Demand at 22 °C outdoors.

## Expected result
- 1: 812.5 W / 30.5 K = 26.64 W/K.
- 2: 426.2 W.
- 3: 0 W (never negative).

## Why it matters
These numbers become the feed-forward of the controller in M3.
