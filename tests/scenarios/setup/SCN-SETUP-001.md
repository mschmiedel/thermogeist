# SCN-SETUP-001: Setting up a house with only the required answers

**Spec:** HAI-001, HAI-002, HAI-004
**Test:** `tests/ha/test_config_flow.py::test_minimal_setup_creates_house`

## Initial state
Home Assistant with an outdoor temperature sensor `sensor.outdoor`.

## Steps
1. Start the Thermogeist setup.
2. Step 1: name "Home", heating type heat pump, outdoor sensor.
3. Step 2: leave everything empty and confirm.

## Expected result
- A config entry "Home" exists.
- The house device has a central mode select set to `auto` and diagnostic sensors; the minimum-opening setting shows 40 %.

## Why it matters
The first impression: three answers and Thermogeist shows up as a device.
