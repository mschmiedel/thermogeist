# SCN-SETUP-002: Missing design temperature is reported at the right field

**Spec:** HAI-002, HAI-018, MDL-003
**Test:** `tests/ha/test_config_flow.py::test_heat_load_without_design_temperature_shows_error`

## Initial state
As in SCN-SETUP-001, step 1 completed.

## Steps
1. Step 2: answer that the heat load is known. Heat load step: enter 8 kW, leave the design
   temperature empty, confirm.
2. Enter −12 °C and confirm again.

## Expected result
- After step 1 the form is shown again with the error `design_temperature_required` on the design temperature field.
- After step 2 the entry is created with both values.

## Why it matters
Errors appear next to the field that needs attention, in the user's language.
