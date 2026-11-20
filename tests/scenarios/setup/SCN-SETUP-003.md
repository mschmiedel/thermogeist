# SCN-SETUP-003: Changing the heating type later updates the profile

**Spec:** HAI-003, CTL-013
**Test:** `tests/ha/test_config_flow.py::test_options_change_heating_type`

## Initial state
A house set up as heat pump.

## Steps
1. Open the options and change the heating type to boiler.

## Expected result
- The integration reloads.
- The minimum-opening setting shows 0 %.

## Why it matters
Users can correct their setup at any time without removing and re-adding the house.
