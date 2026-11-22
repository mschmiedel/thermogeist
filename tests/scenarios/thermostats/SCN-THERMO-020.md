# SCN-THERMO-020: An unknown thermostat is detected from Zigbee2MQTT

**Spec:** ACT-034, ACT-038
**Test:** `tests/ha/test_thermostats.py::test_unknown_thermostat_is_detected_from_z2m`

## Initial state
The MQTT integration runs; Zigbee2MQTT has published `zigbee2mqtt/bridge/devices` with a
thermostat model Thermogeist has no profile for.

## Steps
1. Add this thermostat to a room.

## Expected result
- The roles are pre-filled from its exposes (valve position, minimum opening, external
  temperature).
- The dialog shows "Detected from Zigbee2MQTT (not tested)" as profile.

## Why it matters
Users of other thermostats get the valve strategy without waiting for a profile.
