# SCN-HOUSE-009: The house shows demand and supply of its rooms

**Spec:** MDL-052 to MDL-054
**Test:** `tests/ha/test_estimated_output.py::test_house_shows_demand_and_supply_of_rooms`

## Initial state
As SCN-ROOMS-013: one room with a Bosch thermostat (700 W), valve reported at 39 %.

## Steps
1. Read *Heat demand of rooms*, *Estimated radiator output of rooms* and *Heat from devices
   of rooms* on the house.

## Expected result
- They equal the room's heat demand, its estimated radiator output and 0 W from devices, with
  `rooms: 1` and no room without estimate.

## Why it matters
Users see at a glance whether the rooms get what they need, and can compare the radiators
with the heat pump's output over the long term.
