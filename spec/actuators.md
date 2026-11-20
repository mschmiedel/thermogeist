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
| ACT-033 | Every resolved role is shown pre-filled in the dialog and can be changed or cleared by the user. The chosen profile is shown on the thermostat. | implemented |
| ACT-034 | Later: read the full expose list from Zigbee2MQTT (`zigbee2mqtt/bridge/devices`) to suggest profiles for unknown devices. Requires the MQTT integration. | planned |

Initial profiles: Sonoff TRVZB, Sonoff TRV-ZBT (Gen2), Bosch BTH-RA.

## Strategies

| ID | Strategy | When | Status |
|---|---|---|---|
| ACT-010 | Direct valve control | `valve_write` available | planned |
| ACT-011 | Setpoint modulation | setpoint only, but device temperature readable; gain k is learned | planned |
| ACT-012 | Time-proportional | setpoint only, nothing else reliable | planned |
| ACT-013 | The active strategy and its resolution are visible per room (e.g. "setpoint modulation, ±15 %") | always | planned |
| ACT-014 | Observe mode (default for new rooms): the controller runs and shows the planned position and reason, but nothing is written to the device. Control is switched on per room (M4). | always | implemented |
| ACT-015 | In observe mode each thermostat with `valve_read` shows its actual valve position next to the planned one, so users can compare Thermogeist with their current regulation. | always | implemented |

## Devices

### Sonoff TRVZB (Zigbee2MQTT) – primary target

| ID | Implementation | Status |
|---|---|---|
| ACT-100 | Setpoint on the TRV = room setpoint (display stays honest). | planned |
| ACT-101 | `valve_opening_degree` = position while heating (from the controller). | planned |
| ACT-102 | `valve_closing_degree` = 100 − minimum opening (fallback, works without HA). | planned |
| ACT-103 | `external_temperature_input` + `temperature_sensor_select: remote_temperature`, fallback via `remote_source_offline`. | planned |
| ACT-104 | `smart_temperature_control` off, built-in schedule off, built-in window detection off. | planned |
| ACT-105 | Firmware ≥ 1.1.4 for valve degrees, ≥ 1.3.0 for `temperature_accuracy`. Older firmware is detected and reported. | planned |

### Sonoff TRV-ZBT (Gen2, Zigbee2MQTT)

| ID | Implementation | Status |
|---|---|---|
| ACT-110 | Like TRVZB, using `heating_valve_position` / `idle_valve_position` (not inverted) and `valve_travel_calibration`. | planned |

### Bosch Radiator Thermostat II (BTH-RA, Zigbee2MQTT)

| ID | Implementation | Status |
|---|---|---|
| ACT-120 | Valve position via `pi_heating_demand` (read and write). Whether the device holds the position is open (see open-questions.md). | planned |
| ACT-121 | Send `remote_temperature` at least every 30 min, otherwise the device falls back to its own sensor. | planned |
| ACT-122 | Calibration via `valve_adapt_process`, status via `valve_adapt_status`. | planned |
| ACT-123 | No minimum opening on the device: when HA is down, the device regulates on its own. Shown as a limitation in the UI. | planned |
| ACT-124 | Detect manual operation via `setpoint_change_source`. | planned |

### Generic `climate` entity

| ID | Implementation | Status |
|---|---|---|
| ACT-130 | Setpoint-based kind; strategy setpoint modulation or time-proportional follows in M4. | planned |
