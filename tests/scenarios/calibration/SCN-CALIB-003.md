# SCN-CALIB-003: A thermostat that lost its calibration raises a repair issue

**Spec:** DIA-024
**Test:** `tests/ha/test_calibration.py::test_lost_calibration_raises_an_issue`

## Initial state
Sonoff TRVZB in a room, `closing_steps` 336, resting at its minimum opening: valve position 30 %.

## Steps
1. `closing_steps` becomes 0 (firmware update) and stays so for 11 minutes.
2. It becomes 337 (the button was pressed, the thermostat calibrated itself).

## Expected result
- 1. raises the repair issue *… is not calibrated*, the valve position shows unknown, the logbook names the thermostat.
- 2. removes the issue at once; the valve position is shown again.

## Why it matters
Field finding: after a firmware update the living room valve stayed fully open all night while Thermogeist showed 7 %.
