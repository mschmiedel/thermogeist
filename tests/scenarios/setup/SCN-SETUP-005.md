# SCN-SETUP-005: Two houses in one Home Assistant

**Spec:** HAI-002
**Test:** `tests/ha/test_config_flow.py::test_two_houses_can_be_added`

## Initial state
A house "Home" is already set up.

## Steps
1. Set up a second house "Granny flat" with boiler heating.

## Expected result
- Two config entries exist, each with its own device and entities.

## Why it matters
A granny flat or a holiday home with its own heating can be managed in the same installation.
