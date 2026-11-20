# SCN-HOUSE-002: A heat load needs a design outdoor temperature

**Spec:** MDL-002, MDL-003
**Test:** `tests/core/test_house.py::test_heat_load_requires_design_temperature`

## Initial state
A minimal house as in SCN-HOUSE-001.

## Steps
1. Add a heat load of 8 kW without a design outdoor temperature and validate.
2. Add a design outdoor temperature of −12 °C and validate again.

## Expected result
- Step 1: one issue `design_temperature_required` on the field `design_outdoor_temperature`.
- Step 2: no issues.

## Why it matters
A heat load is only meaningful together with the outdoor temperature it was calculated for. The user is told exactly which field is missing.
