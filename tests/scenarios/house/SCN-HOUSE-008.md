# SCN-HOUSE-008: No heating water sensors without source sensors

**Spec:** DIA-042
**Test:** `tests/ha/test_house_sensors.py::test_no_water_sensors_without_sources`

## Initial state
House without flow and return sensors.

## Steps
1. Load the house.

## Expected result
- No flow, return or spread sensor; room coverage exists.

## Why it matters
No empty sensors for things the user has not configured.
