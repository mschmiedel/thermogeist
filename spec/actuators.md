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
| ACT-009 | `setpoint_source` | device reports where a setpoint came from | rejected: Thermogeist detects changes on the device by comparing with the value it last wrote (OVR-001), which works with every thermostat and needs no extra field; with the setpoint strategy the display is ignored anyway (OVR-004) |

| ID | Kind | Requirement | Status |
|---|---|---|---|
| ACT-020 | Setpoint-based | Only `climate` is required. Works with every thermostat. | implemented |
| ACT-021 | Valve-based | `valve_write` is set and the strategy is not *setpoint* (ACT-050). Enables direct valve control (ACT-010). | implemented |

## Device profiles

| ID | Requirement | Status |
|---|---|---|
| ACT-030 | Profiles are JSON files in `custom_components/thermogeist/device_profiles/`, one per model: matching rules (manufacturer, model id), kind, role mapping per source (`z2m`; `zha` later), quirks and documentation notes. Contributions via pull request. | implemented |
| ACT-031 | When a thermostat is assigned, Thermogeist reads manufacturer and model id from the HA device registry and picks the matching profile; without a match it suggests the setpoint-based kind. | implemented |
| ACT-032 | Roles are resolved to entities of that device: the `climate` role by domain, the others by the Zigbee2MQTT expose name contained in the entity's unique id (`<ieee>_<expose>_zigbee2mqtt`). | implemented |
| ACT-033 | Every resolved role is shown pre-filled in the dialog and can be changed or cleared by the user. Any entity of a fitting domain may be chosen, also from another device (some integrations, e.g. Bosch Smart Home, put climate and valve entities on separate devices). The chosen profile is shown on the thermostat. | implemented |
| ACT-035 | Each role is checked for plausibility when saving: valve roles need a percentage (unit %), the external temperature a temperature. Implausible choices are rejected at the field with an explanation. | implemented |
| ACT-036 | The entity chosen for `valve_write` cannot also be chosen for `valve_read`: it usually only echoes what Thermogeist wrote and is no valve position. Exception: the device profile maps both roles to the same entity because the device keeps regulating that value itself (Bosch BTH-RA `pi_heating_demand`). The dialog rejects it at the field with an explanation. | implemented |
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
| ACT-016 | A thermostat without `valve_read` but with `valve_write` and `valve_min` (Sonoff TRVZB, TRV-ZBT) has its valve position derived: the opening position while its climate entity reports `hvac_action: heating`, the closing position (inverted if the profile says so) while it reports `idle` or `off`, unknown otherwise. Such devices move between the two positions with their own controller and report no valve position. The *Valve position* entity shows it with `source: derived` and the `hvac_action`; the estimated output (MDL-013) and the sizing operation check (DIA-015) use it. The controller start after a restart (CTL-044) still uses reported positions only. | always | implemented |

## Setpoint strategy (first version)

| ID | Requirement | Status |
|---|---|---|
| ACT-050 | Per thermostat a control strategy: *automatic* (valve if `valve_write` exists, else setpoint), *valve* or *setpoint*. Shown on the thermostat. | implemented |
| ACT-051 | Setpoint strategy with external temperature input: the room temperature is sent to the device and its setpoint is the room target; the device regulates on the real room temperature with its own controller. | implemented |
| ACT-052 | Setpoint strategy without external input: the device setpoint is the room target plus the measured difference between the device's own temperature and the room sensor (30-minute average), so the device aims at the right room temperature. Limited to 5–30 °C, rounded to 0.5 K. The device display then shows the corrected value. | implemented |
| ACT-053 | Setpoint writes are bundled like valve writes: only changes of at least 0.5 K, at most every 10 minutes; window, stop and safety at once (window/stop: 5 °C). | implemented |
| ACT-054 | Limits of the setpoint strategy are explicit: no minimum opening and no calm valve movement – the device's own controller decides. Shown on the thermostat (`strategy: setpoint`). | implemented |
| ACT-055 | While the room should heat, a thermostat whose climate entity is in mode `off` is switched back to `heat` before its setpoint is written, and the setpoint is written again. Bosch Smart Home switches its room climate to `off` when it gets 5 °C (window, stop); a later setpoint alone does not switch it back. | implemented |

## On/off heaters

Heaters that are only switched on or off: a smart plug or relay in front of a fan convector, an
infrared panel, an electric towel rail. Deliberately generic; special cases (several stages,
residual heat) are built by the user with template entities instead of extra product features.

| ID | Requirement | Status |
|---|---|---|
| ACT-060 | A thermostat kind *on/off*: a switch entity (required). Added through the room's gear menu like every thermostat. | planned |
| ACT-061 | Energy source per heater: *heating circuit* (output depends on the flow temperature like a radiator, MDL-012; the house's heating type and flow sensor apply) or *direct* (fixed output, independent of the flow temperature, e.g. infrared). Without it the feed-forward and the house balance would mix up heating water and electricity. | planned |
| ACT-062 | Heat output: a rated output in W (for *heating circuit* at 75/65/20 °C like radiators), or optionally an entity with the current heat output in W that replaces it – typically a template sensor built by the user. Thermogeist has no built-in stage logic. Test scenario (not a rule): a template sensor that derives the heat output of a two-stage plinth heater from its fan power (field values: off 0 W, stage 1 ≈ 11 W, stage 2 ≈ 23 W). Heat a heater releases while off (e.g. water flowing through a plinth heater) is entered as a heat source of the room (MDL-040). | planned |
| ACT-063 | Control by time-proportional switching: duty cycle = demand / heat output (corrected by the slow controller), over a cycle of 20 min (named constant) with minimum on and off times of 5 min each (named constant), so relay and fan do not switch every minute. Window, stop and safety switch off at once; the frost guard (RUL-015) switches on. | planned |
| ACT-064 | Optional power sensor for fault detection: switched on for 3 minutes (named constant) but the measured power stays near 0 W (below 2 W, named constant) → problem binary sensor (for the user's own notifications), repair issue and logbook entry; while the problem lasts no heat is counted for this heater. Cleared as soon as power is measured again. | planned |
| ACT-065 | The heater shows `duty_cycle_pct`, `on_since`/`off_since`, the heat output used and its source (rated or entity). | planned |

## Control mode (M4)

| ID | Requirement | Status |
|---|---|---|
| ACT-040 | Per room a switch "Control" (default off = observe). Only rooms with control on write to their thermostats. The state survives restarts. | implemented |
| ACT-041 | Valve-based thermostats get, while controlled: the planned position on `valve_write` (only when it differs by at least 1 %), the minimum opening on `valve_min` (inverted if the profile says so), the room temperature on `external_temperature` (on change by ≥ 0.1 K and at least every 20 min), and the room target as setpoint on the climate entity so the display stays honest. Central stop sets the valve to 0 %. | implemented |
| ACT-042 | Profiles may list device settings needed for control (e.g. Bosch `operating_mode: manual`, Sonoff `smart_temperature_control: off`, `temperature_sensor_select: remote_temperature`). They are applied when control starts; the previous values are stored and restored when control stops or the thermostat is removed (ACT-008). | implemented |
| ACT-043 | Write verification: if a valve-based thermostat reports a position more than 5 % away from the last written one for longer than 5 minutes, Thermogeist writes again, at most 3 times per hour. If that is exceeded, the room switches back to observe, the logbook explains why (`device_overrides_valve`) and a repair issue appears. | implemented |
| ACT-044 | Setpoint-based thermostats are controlled with the setpoint strategy (ACT-050 to ACT-054). | implemented |
| ACT-047 | Valve confirmation per thermostat: "Confirm valve position every … minutes" in the thermostat dialog, pre-filled from the profile (`valve_write_refresh_minutes`; Bosch BTH-RA: 10), empty = off. The unchanged position is resent at that interval; confirmations do not count as rewrites (ACT-043). Field finding: the Bosch drops an external valve position exactly 15 minutes after the last write. | implemented |
| ACT-048 | Each thermostat shows what Thermogeist did: `last_write` (time) and `last_write_value`, `last_confirmation`, `rewrites_last_hour`, `valve_refresh_minutes` – as attributes of its kind sensor. | implemented |
| ACT-046 | Valve writes are bundled to spare motor and battery: a new position is written when it differs by at least 3 % and the last write is at least 10 min ago, or by at least 1 % after 30 min. Window, stop and safety are written at once, and so is the way back (window closed again). Field finding: 1 % steps every 3 minutes during a ramp were too many. | implemented |
| ACT-045 | Writes only start 90 s after Home Assistant started (`startup_hold`), so devices are available and no stale values are sent. | implemented |

## Devices

### Sonoff TRVZB (Zigbee2MQTT) – primary target

| ID | Implementation | Status |
|---|---|---|
| ACT-100 | Setpoint on the TRV = room setpoint (display stays honest). | implemented |
| ACT-101 | `valve_opening_degree` = position while heating (from the controller). | implemented |
| ACT-102 | `valve_closing_degree` = 100 − minimum opening (fallback, works without HA). Whenever the planned position is below the minimum opening (room clearly too warm, CTL-037, held there by CTL-043, window, central stop), it follows the planned position, because the device rests on it as long as the room is above its setpoint; once the plan is back at or above the minimum it returns to the minimum opening. | implemented |
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
| ACT-120 | Valve position via `pi_heating_demand` (read and write) in `operating_mode: manual`; the device keeps it for 15 minutes, so it is confirmed every 10 minutes (ACT-047). | implemented |
| ACT-121 | Send `remote_temperature` at least every 30 min, otherwise the device falls back to its own sensor. | implemented |
| ACT-122 | Calibration via `valve_adapt_process`, status via `valve_adapt_status`. | planned |
| ACT-123 | No minimum opening on the device: when HA is down, the device regulates on its own. Shown as a limitation in the UI. | planned |
| ACT-124 | Detect manual operation via `setpoint_change_source`. | rejected (see ACT-009) |

### Generic `climate` entity

| ID | Implementation | Status |
|---|---|---|
| ACT-130 | Setpoint-based kind; strategy setpoint modulation or time-proportional follows in M4. | planned |
