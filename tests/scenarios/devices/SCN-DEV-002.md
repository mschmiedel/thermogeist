# SCN-DEV-002: The Bosch Smart Home model reproduces two recorded days

**Spec:** TST-012
**Test:** `tests/core/test_device_models.py::test_shc_model_reproduces_the_recorded_days`

## Initial state
`bosch_shc_day.csv` and `bosch_shc_day2.csv`: two days of a Bosch Smart Home thermostat (first generation) in a dining room, setpoints sent by Thermogeist, with window openings.

## Steps
1. Replay each day through `ShcModel`, starting from its first recorded state.

## Expected result
- The model's valve differs by at most 4 % on average on each day (fitted: 3.1 % and 2.7 %).

## Why it matters
Field behaviour kept for testing after the device is gone: a proportional band of 30 % per kelvin, never below 23 %, corrections of 10 % or more at most every 20 minutes.
