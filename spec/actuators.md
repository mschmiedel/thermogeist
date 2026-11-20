# Actuators (thermostats)

A thermostat is described by **roles**: which Home Assistant entity does what. Two generic kinds
cover every device; **device profiles** fill in the roles for known models and stay editable.
The controller always outputs a heat demand of 0–100 % (ARC-004); the roles decide how it is
applied.

## Roles and kinds

| ID | Role | Meaning | Status |
|---|---|---|---|
| ACT-001 | `climate` (required) | the thermostat's climate entity: setpoint, local temperature | implemented |
| ACT-002 | `valve_read` | valve position can be read (%) | implemented |
| ACT-003 | `valve_write` | valve position while heating can be set (%) | implemented |
| ACT-004 | `valve_min` | minimum opening stored on the device, a fallback that works without HA. A profile can mark it as inverted (the device stores the closing degree, minimum opening = 100 − value). | implemented |
| ACT-005 | `external_temperature` | external room temperature can be passed to the device | implemented |
| ACT-006 | `child_lock` | child lock can be switched | implemented |
| ACT-007 | `calibration_trigger`, `calibration_status` | stroke calibration can be started and followed | implemented |
| ACT-009 | `setpoint_source` | device reports where a setpoint came from | implemented |

| ID | Kind | Requirement | Status |
|---|---|---|---|
| ACT-020 | Setpoint-based | Only `climate` is required. Works with every thermostat. | implemented |
| ACT-021 | Valve-based | `valve_write` is set. Enables direct valve control (ACT-010). | implemented |

## Device profiles

| ID | Requirement | Status |
|---|---|---|
| ACT-030 | Profiles are JSON files in `custom_components/thermogeist/device_profiles/`, one per model: matching rules (manufacturer, model id), kind, role mapping per source (`z2m`; `zha` later), quirks and documentation notes. Contributions via pull request. | implemented |
| ACT-031 | When a thermostat is assigned, Thermogeist reads manufacturer and model id from the HA device registry and picks the matching profile; without a match it suggests the setpoint-based kind. | implemented |
| ACT-032 | Roles are resolved to entities of that device: the `climate` role by domain, the others by the Zigbee2MQTT expose name contained in the entity's unique id (`<ieee>_<expose>_zigbee2mqtt`). | implemented |
| ACT-033 | Every resolved role is shown pre-filled in the dialog and can be changed or cleared by the user. Any entity of a fitting domain may be chosen, also from another device (some integrations, e.g. Bosch Smart Home, put climate and valve entities on separate devices). The chosen profile is shown on the thermostat. | implemented |
| ACT-035 | Each role is checked for plausibility when saving: valve roles need a percentage (unit %), the external temperature a temperature, the setpoint source an entity reporting `manual` / `schedule` / `externally`. Implausible choices are rejected at the field with an explanation. | implemented |
| ACT-034 | Later: read the full expose list from Zigbee2MQTT (`zigbee2mqtt/bridge/devices`) to suggest profiles for unknown devices. Requires the MQTT integration. | planned |

Initial profiles: Sonoff TRVZB, Sonoff TRV-ZBT (Gen2), Bosch BTH-RA.

## Strategies

| ID | Strategy | When | Status |
|---|---|---|---|
| ACT-010 | Direct valve control | `valve_write` available | implemented |
| ACT-011 | Setpoint modulation | setpoint only, but device temperature readable; gain k is learned | planned |
| ACT-012 | Time-proportional | setpoint only, nothing else reliable | planned |
| ACT-013 | The active strategy and its resolution are visible per room (e.g. "setpoint modulation, ±15 %") | always | planned |
| ACT-014 | Observe mode (default for new rooms): the controller runs and shows the planned position and reason, but nothing is written to the device. Control is switched on per room (M4). | always | implemented |
| ACT-015 | In observe mode each thermostat with `valve_read` shows its actual valve position next to the planned one, so users can compare Thermogeist with their current regulation. | always | implemented |

## Control mode (M4)

| ID | Requirement | Status |
|---|---|---|
| ACT-040 | Per room a switch "Control" (default off = observe). Only rooms with control on write to their thermostats. The state survives restarts. | implemented |
| ACT-041 | Valve-based thermostats get, while controlled: the planned position on `valve_write` (only when it differs by at least 1 %), the minimum opening on `valve_min` (inverted if the profile says so), the room temperature on `external_temperature` (on change by ≥ 0.1 K and at least every 20 min), and the room target as setpoint on the climate entity so the display stays honest. Central stop sets the valve to 0 %. | implemented |
| ACT-042 | Profiles may list device settings needed for control (e.g. Bosch `operating_mode: manual`, Sonoff `smart_temperature_control: off`, `temperature_sensor_select: remote_temperature`). They are applied when control starts; the previous values are stored and restored when control stops or the thermostat is removed (ACT-008). | implemented |
| ACT-043 | Write verification: if a valve-based thermostat reports a position more than 5 % away from the last written one for longer than 5 minutes, Thermogeist writes again, at most 3 times per hour. If that is exceeded, the room switches back to observe, the logbook explains why (`device_overrides_valve`) and a repair issue appears. | implemented |
| ACT-044 | Setpoint-based thermostats are not controlled yet in M4; their rooms cannot be switched to control (the switch explains why). | implemented |
| ACT-046 | Valve writes are bundled to spare motor and battery: a new position is written when it differs by at least 3 % and the last write is at least 10 min ago, or by at least 1 % after 30 min. Window, stop and safety are written at once, and so is the way back (window closed again). Field finding: 1 % steps every 3 minutes during a ramp were too many. | implemented |
| ACT-045 | Writes only start 90 s after Home Assistant started (`startup_hold`), so devices are available and no stale values are sent. | implemented |

## Devices

### Sonoff TRVZB (Zigbee2MQTT) – primary target

| ID | Implementation | Status |
|---|---|---|
| ACT-100 | Setpoint on the TRV = room setpoint (display stays honest). | implemented |
| ACT-101 | `valve_opening_degree` = position while heating (from the controller). | implemented |
| ACT-102 | `valve_closing_degree` = 100 − minimum opening (fallback, works without HA). | implemented |
| ACT-103 | `external_temperature_input` + `temperature_sensor_select: remote_temperature`, fallback via `remote_source_offline`. | implemented |
| ACT-104 | `smart_temperature_control` off, built-in schedule off, built-in window detection off. | implemented |
| ACT-105 | Firmware ≥ 1.1.4 for valve degrees, ≥ 1.3.0 for `temperature_accuracy`. Older firmware is detected and reported. | planned |

### Sonoff TRV-ZBT (Gen2, Zigbee2MQTT)

| ID | Implementation | Status |
|---|---|---|
| ACT-110 | Like TRVZB, using `heating_valve_position` / `idle_valve_position` (not inverted) and `valve_travel_calibration`. | planned |

### Bosch Radiator Thermostat II (BTH-RA, Zigbee2MQTT)

| ID | Implementation | Status |
|---|---|---|
| ACT-120 | Valve position via `pi_heating_demand` (read and write). Whether the device holds the position is open (see open-questions.md). | implemented |
| ACT-121 | Send `remote_temperature` at least every 30 min, otherwise the device falls back to its own sensor. | implemented |
| ACT-122 | Calibration via `valve_adapt_process`, status via `valve_adapt_status`. | planned |
| ACT-123 | No minimum opening on the device: when HA is down, the device regulates on its own. Shown as a limitation in the UI. | planned |
| ACT-124 | Detect manual operation via `setpoint_change_source`. | planned |

### Generic `climate` entity

| ID | Implementation | Status |
|---|---|---|
| ACT-130 | Setpoint-based kind; strategy setpoint modulation or time-proportional follows in M4. | planned |
