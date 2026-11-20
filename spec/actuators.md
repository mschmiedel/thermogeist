# Actuators (adapters)

An adapter translates the heat demand (0–100 %) into commands for a specific device. It reports
what the device can do and encapsulates quirks such as calibration or child lock.

## Capability model

| ID | Capability | Meaning | Status |
|---|---|---|---|
| ACT-001 | `valve_write` | valve position can be set directly | planned |
| ACT-002 | `valve_read` | valve position can be read | planned |
| ACT-003 | `valve_min_on_device` | minimum opening can be stored on the device (fallback when HA is down) | planned |
| ACT-004 | `external_temperature` | external room temperature can be passed, with fallback to the built-in sensor | planned |
| ACT-005 | `calibration_trigger` | stroke calibration can be triggered by command, status readable | planned |
| ACT-006 | `child_lock` | child lock can be set | planned |
| ACT-007 | `setpoint_source` | device reports where a setpoint came from (manual, schedule, external) | planned |
| ACT-008 | Preconditions | adapter states what an action requires (e.g. child lock off before calibration) and restores the state afterwards – also after a restart | planned |

## Strategies

| ID | Strategy | When | Status |
|---|---|---|---|
| ACT-010 | Direct valve control | `valve_write` available | planned |
| ACT-011 | Setpoint modulation | setpoint only, but device temperature readable; gain k is learned | planned |
| ACT-012 | Time-proportional | setpoint only, nothing else reliable | planned |
| ACT-013 | The active strategy and its resolution are visible per room (e.g. "setpoint modulation, ±15 %") | always | planned |
| ACT-014 | Observe mode (default for new rooms): the controller runs and shows the planned position and reason, but nothing is written to the device. Control is switched on per room. | always | planned |

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
| ACT-110 | Like TRVZB, using `heating_valve_position` / `idle_valve_position` and `valve_travel_calibration`. | planned |

### Bosch Radiator Thermostat II (BTH-RA, Zigbee2MQTT)

| ID | Implementation | Status |
|---|---|---|
| ACT-120 | Valve position via `pi_heating_demand`. Whether the device holds the position is open (see open-questions.md). | planned |
| ACT-121 | Send `remote_temperature` at least every 30 min, otherwise the device falls back to its own sensor. | planned |
| ACT-122 | Calibration via `valve_adapt_process`, status via `valve_adapt_status`. | planned |
| ACT-123 | No minimum opening on the device: when HA is down, the device regulates on its own. Shown as a limitation in the UI. | planned |
| ACT-124 | Detect manual operation via `setpoint_change_source`. | planned |

### Generic `climate` entity

| ID | Implementation | Status |
|---|---|---|
| ACT-130 | Setpoint modulation or time-proportional, depending on readable attributes. | planned |
