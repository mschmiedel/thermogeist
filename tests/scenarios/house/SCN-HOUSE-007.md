# SCN-HOUSE-007: Heating water and room coverage on the house

**Spec:** DIA-042, MDL-046
**Test:** `tests/ha/test_house_sensors.py::test_heating_water_and_coverage`

## Initial state
House with 160 m² living area, flow 40 °C and return 34 °C sensors; one room of 20 m².

## Steps
1. Load the house.

## Expected result
- Flow 40 °C, return 34 °C, spread 6 K (with the source sensors as attributes).
- Room coverage = 100 % − heat load not assigned to a room; `rooms: 1`,
  `floor_area_not_in_rooms_m2: 140`.

## Why it matters
Users see the water the controller works with, and how much of the house still lacks rooms.
