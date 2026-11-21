# SCN-HOUSE-009: The house shows demand and supply of its rooms

**Spec:** MDL-052, MDL-053
**Test:** `tests/ha/test_estimated_output.py::test_house_shows_demand_and_supply_of_rooms`

## Initial state
As SCN-ROOMS-013: one room with a Bosch thermostat (700 W), valve reported at 39 %.

## Steps
1. Read *Heat demand of rooms* and *Heat supply of rooms* on the house.

## Expected result
- Demand equals the room's heat demand; supply equals its estimated radiator output (no
  devices), with `rooms: 1` and no room without estimate.

## Why it matters
Users see at a glance whether the house's rooms get what they need right now.
