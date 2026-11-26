# SCN-HEATER-008: The current stage comes from the sensor, the setter or the switch

**Spec:** ACT-066
**Test:** `tests/core/test_heater.py::test_current_stage_sources`

## Initial state
Three heaters: one with stage sensor, one with stage setter only, one plain on/off heater.

## Steps
1. Read the sensor values "2", "1.0", "1.5", "7" and "unavailable" for the first heater.
2. Switch the second heater on with the setter at 2, and off.
3. Switch the third heater on and off.

## Expected result
1. 2, 1, unknown, unknown, unknown – source `stage_sensor`.
2. Stage 2 (`stage_setter`), then 0 (`switch`).
3. Stage 1, then 0 (`switch`).

## Why it matters
The heat Thermogeist counts depends on the stage; a template that reports something odd must
not turn into a made-up stage.
