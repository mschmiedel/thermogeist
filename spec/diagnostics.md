# Diagnostics

## Radiator sizing per room

Can the radiators of a room hold its setpoint on the design day? Two sources:

1. **Static** from inputs (MDL-015): the room's demand on the design day compared with what its
   radiators deliver at the flow temperature of that day. The flow temperature is never asked
   for; it comes from the learned heating curve (DIA-014).
2. **Operation:** the valve stays wide open in cold weather and the room still does not reach its
   setpoint (DIA-015). This can only say "undersized"; it wins over the static result.

Later: extrapolate the average opening of steady phases to the design day (DIA-006).

| ID | Classification | Criterion | Status |
|---|---|---|---|
| DIA-001 | heavily oversized | load on the design day < 30 % of the radiator output | implemented |
| DIA-002 | right size | 30–90 % | implemented |
| DIA-003 | tight | 90–100 % | implemented |
| DIA-004 | undersized | > 100 %, or the operation check (DIA-015) | implemented |
| DIA-005 | not assessable | heat load, radiator output or flow temperature (sensor or entered heating curve, MDL-019) missing, or the heating curve not learned yet; the attribute `missing` says what is missing | implemented |
| DIA-006 | (empirical) | Average opening in steady phases plotted against the outdoor temperature and extrapolated to the design day, with precedence over the static result. Needs at least 5 steady days below 5 °C. | planned |

Load on the design day = `H · (setpoint − design outdoor temperature) / available output`, where
`H` is the heat loss coefficient (MDL-010), the setpoint is the room's own setpoint (what the
user wants, not the design indoor temperature), and the available output is MDL-012 at the
learned design-day flow, with the room at its setpoint and the spread the controller uses
(measured, else 5 K). Devices that heat the room (MDL-040) are not counted: they cannot be relied
on. The oversizing factor (MDL-015) is the inverse: available output / demand.

| ID | Requirement | Status |
|---|---|---|
| DIA-010 | The message depends on the profile. With a heat pump, oversizing is a reserve, not a fault (attribute `note: reserve`, no repair issue). | implemented |
| DIA-011 | If all assessable rooms (at least 2) are heavily oversized, a house-level repair issue says the flow temperature is probably higher than needed, without touching the heating system. For every profile: with a heat pump a lower flow saves the most. | implemented |
| DIA-012 | Per room with thermostats a sensor *Radiator size* (`radiator_sizing`, enum of DIA-001 to DIA-005) with attributes `load_pct`, `factor`, `confidence`, `basis` (`static` or `operation`), `cause`, `design_flow_c`, `design_demand_w`, `design_output_w`, `full_open_hours` and, if any, `missing` and `note`. Recomputed every hour and at start-up. | implemented |
| DIA-013 | Repair issues with a link to the FAQ entry: *undersized* for every profile; *heavily oversized* only for boiler and direct electric (DIA-010); the house-level issue of DIA-011. An issue disappears as soon as its condition is gone. | implemented |
| DIA-014 | Learned heating curve: once per hour the median flow (plausible values, CTL-039) and the mean outdoor temperature of that hour, only while heating ran (median flow at least 5 K above the mean room temperature of the house, `HEATING_RUNNING_MARGIN_K`). A straight line through the hours of the last 60 days (least squares) gives the flow at the design outdoor temperature. Learned once there are at least 48 hours and the outdoor temperatures span at least 5 K, and the line falls with rising outdoor temperature; until then "not assessable". `confidence` from how far the line is extended below the coldest hour seen: up to 5 K *high*, up to 15 K *medium*, beyond *low*. The hours survive restarts. House sensor *Flow on the design day* with `slope_k_per_k`, `hours`, `outdoor_min_c`, `outdoor_max_c` and `confidence`. Without a flow sensor the entered heating curve (MDL-019) takes the place of the learned one: confidence high, attributes `source: heating_curve` and the two points. | implemented |
| DIA-015 | Operation check: an hour counts as "fully open in the cold" when for at least 90 % of its minutes the valve was at least 95 % open, the room was more than 0.5 K below its target, the outdoor temperature was below 5 °C and the active reason was `setpoint`. The valve is the reported position if a thermostat reports one, else the planned position while Thermogeist controls the room; in observe mode without a reported position the hour does not count. At least 6 such hours in the last 7 days mean *undersized* with `basis: operation`. The hours survive restarts. | implemented |

`cause` names the probable cause (see below): `radiator_small` when the static result is
undersized, `input_or_hydraulics` when only the operation check says undersized (DIA-023),
`flow_high` for heavily oversized rooms when all rooms are (DIA-011), `radiator_large` for other
heavily oversized rooms.

## House balance

| ID | Requirement | Status |
|---|---|---|
| DIA-040 | Compare measured house heat output (MDL-017) with the sum of learned room losses plus the share outside Thermogeist. Show how much of the heat the room models explain, and hint when MDL-009 looks wrong. | planned |
| DIA-041 | Heat output clearly above room demand while rooms stay cold points to losses outside the rooms (e.g. pipes in an unheated basement). | planned |
| DIA-042 | The heating water is visible on the house device: flow, return and spread as sensors (only those whose source sensors are configured; spread needs both), showing the averaged values the controller actually uses (not the raw sensors), with the source entity as attribute. | implemented |

## Distinguishing causes

| ID | Data | Probable cause | Status |
|---|---|---|---|
| DIA-020 | Valve 100 %, room cold, other rooms fine | presetting too closed, hydraulics | planned |
| DIA-021 | Valve 100 %, pipe stays cold (calibration probe) | air, stuck valve pin, TRV not opening | planned |
| DIA-022 | One room needs a lot, others little | uneven distribution | planned |
| DIA-023 | Statically fine, empirically too small | wrong input, radiator covered, presetting too closed (`cause: input_or_hydraulics`) | implemented |
| DIA-024 | The thermostat itself reports heating (`hvac_action: heating`, reported or derived valve clearly open) for at least an hour, the flow is well above the room, no window is open, but the room temperature does not rise | thermostat not opening: lost calibration, stuck pin. Repair issue per thermostat with the hint to recalibrate. Thresholds to be derived from field data; false alarms to rule out: radiator too small in severe cold, airing without contact, very slow rooms. Field finding: a Sonoff TRVZB lost its calibration after a firmware update while Zigbee2MQTT and Home Assistant reported it as fine. | planned |

## Hydraulic balancing (staged)

| ID | Stage | Status |
|---|---|---|
| DIA-030 | Stage 1: identify the critical room, relative suggestions for presettings, applied manually. Refers to professional balancing (procedure B). | planned |
| DIA-031 | Stage 2: automatic limit on maximum opening during heat-up so all rooms arrive at the same time. | planned |
| DIA-032 | Stage 3: continuous dynamic balancing via a slow house loop (days). Only after stages 1 and 2 have proven themselves. | planned |
| DIA-033 | Stages 2 and 3 require a hydraulic network in the simulator (pump, pipes, valves). | planned |
