# SCN-HOUSE-001: A house with only the required inputs is valid

**Spec:** MDL-001, MDL-008, MDL-009
**Test:** `tests/core/test_house.py::test_minimal_house_is_valid`

## Initial state
A house named "Home", heating type heat pump, outdoor sensor `sensor.outdoor`. No heat load, no design temperature, no living area.

## Steps
1. Validate the house.

## Expected result
- No validation issues.
- The share outside Thermogeist is 0 %.

## Why it matters
Beginners must get a working setup with three answers. Everything else is optional.
