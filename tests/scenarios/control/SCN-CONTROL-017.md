# SCN-CONTROL-017: Settings a firmware update reset are set again

**Spec:** ACT-049, ACT-042, ACT-104
**Test:** `tests/ha/test_control.py::test_reset_device_settings_are_set_again`

## Initial state
A controlled Sonoff TRVZB; Thermogeist has set `temperature_sensor_select: remote_temperature`,
`temperature_accuracy: -0.2` (factory -1) and sent the room temperature 19.5 °C.

## Steps
1. The thermostat restarts after a firmware update: it reports `local_temperature` and an
   external temperature of 0.
2. One minute later.

## Expected result
- `remote_temperature` is set again and the room temperature 19.5 °C is sent again at once.
- The logbook says which setting was reset.
- A device that never reports anything is not rewritten every minute.
- A device that reports its old value again after the write (the write was lost during the
  update) gets the setting again, at most every 10 minutes.

## Why it matters
After firmware updates three Sonoff fell back to their own sensor next to the radiator; Alex
then rested at 30 % while the room was 0.9 K too cold.
