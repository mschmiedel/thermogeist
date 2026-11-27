# SCN-FW-002: Older firmware raises a warning until the device is updated

**Spec:** ACT-017, ACT-105
**Test:** `tests/ha/test_firmware.py::test_old_firmware_raises_a_warning_until_updated`

## Initial state
A room with a Sonoff TRVZB whose device entry shows firmware 1.1.4; the Sonoff profile names
1.3.0.

## Steps
1. Assign the thermostat to the room.
2. The device entry changes to firmware 1.3.0 (update via the Zigbee bridge).

## Expected result
- After step 1 a repair issue (warning) asks to use at least firmware 1.3.0 and names 1.1.4.
- After step 2 the issue is gone.

## Why it matters
With old firmware the Sonoff lacks `temperature_accuracy` and starts heating only 1 K below its
setpoint, so a room stays too cold without any visible reason.
