# Decisions and reasons

Principle: **no intervention without a visible reason.** Every change to setpoint, mode or valve
is created as a `Decision` at one central place.

## Decision

| Field | Content |
|---|---|
| `code` | stable reason code, e.g. `window_open` |
| `room` | affected room |
| `action` | what changes (setpoint, mode, valve, learning) |
| `params` | values that fill the text (e.g. duration, threshold) |
| `severity` | `info` / `notice` / `safety` |
| `timestamp` | from the `TimeProvider` |
| `source` | rule, controller, limiter, user, device |

## Requirements

| ID | Requirement | Status |
|---|---|---|
| RSN-001 | All reason codes live in one central catalogue (`core/decisions.py`) with severity, translated state names (en/de) and an FAQ page per language. Text templates with parameters follow with the logbook (RSN-003). | implemented |
| RSN-002 | One sensor `active_reason` (enum) per room with the currently effective reason; attributes: severity, since, FAQ link, parameters. | implemented |
| RSN-003 | Every change of a room's reason with `severity ≥ notice`, every adopted manual setpoint and every fallback to observe appears in the HA logbook as a readable sentence. | implemented |
| RSN-004 | A silent room sensor (`safety_sensor_stale`) and a thermostat that overrides its valve (`device_overrides_valve`) raise a repair issue; it disappears once the cause is resolved. | implemented |
| RSN-005 | A test ensures that every code in the catalogue has a translation and an FAQ entry in both languages. | implemented |

## Catalogue (initial set)

| Code | Severity | Example text |
|---|---|---|
| `setpoint` | info | "Holding the setpoint 21.0 °C" |
| `schedule` | info | "Schedule: setpoint 20.0 °C from 06:00" |
| `window_open` | notice | "Window open for 30 s: room set to frost protection" |
| `manual_override_device` | info | "Set to 22.0 °C on the thermostat, valid until 22:00" |
| `manual_override_ha` | info | "Set to 22.0 °C in Home Assistant" |
| `startup_hold` | info | "Home Assistant starting: control waits 90 s for devices" |
| `central_stop` | notice | "Heating stopped for the whole house" |
| `frost_protection` | notice | "Frost protection active: 7.0 °C" |
| `safety_sensor_stale` | safety | "Temperature sensor silent for 62 min (limit 60 min): valve set to minimum opening" |
| `device_overrides_valve` | safety | "Thermostat Gästebad keeps changing its valve position: room switched back to observe" |
| `device_overtemp_guard` | notice | "Room above setpoint: thermostat limits on its own" |
| `learning_paused` | info | "Learning paused (by user)" |
| `calibration_running` | info | "Calibration running: step 4 of 16" |
| `calibration_blocked` | notice | "Calibration not possible: child lock active and cannot be switched" |
| `cannot_reach_setpoint` | notice | "Room cannot reach 21 °C at −5 °C outdoors: radiator too small" |
| `firmware_too_old` | notice | "Firmware 1.0.9 too old for valve control (needs at least 1.1.4)" |
