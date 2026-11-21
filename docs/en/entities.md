# All entities

**English** | [Deutsch](../de/entities.md)

Every entity Thermogeist creates, grouped by device: the **house**, each **room** and the
**thermostats** assigned to a room (their entities sit on the room device). The column *When it
exists* tells you whether you will see the entity at all; *Unknown when* says when it exists but
shows no value. Diagnostic and configuration entities are on the device page under
*Diagnostic* and *Configuration*.

## House

| Entity | Meaning | When it exists | Unknown when |
|---|---|---|---|
| Central mode | *Auto*, *Stop* or *Frost protection* for the whole house. Survives restarts. | always | – |
| Heating type | Heat pump, boiler or direct electric – decides how calmly Thermogeist regulates. Diagnostic. | always | – |
| Heat load | The heat load you entered, in kW: what the house needs on the coldest design day. A fixed planning value, not what is needed right now (see *Heat demand of rooms*). Diagnostic. | always | no heat load entered |
| Design outdoor temperature | The outdoor temperature the heat load was calculated for. Diagnostic. | always | not entered |
| Share outside Thermogeist | Part of the heat load in rooms Thermogeist does not control, as entered. Diagnostic. | always | – |
| Heat load not assigned to a room | Part of the heat load no room (and no share outside) covers yet. Diagnostic. | always | – |
| Room coverage | 100 % minus the part not assigned. Attributes: `missing_pct`, `floor_area_not_in_rooms_m2`, `rooms`. | always | – |
| Heat demand of rooms | Watts your rooms need right now to hold their targets – the sum of their *Heat demand*, over the same rooms as *Heat supply of rooms*. Attributes: `rooms`, `rooms_without_estimate`. | always | no heat load on the house |
| Heat supply of rooms | Watts your rooms get right now: the *Estimated radiator output* plus the *Heat from devices* of all rooms. A room whose radiators cannot be estimated is left out of both sums and named in `rooms_without_estimate`. Attributes: `radiators_w`, `devices_w`, `rooms`, `rooms_without_estimate`. Only rooms in Thermogeist count (see *Room coverage*); this is not the output of your heat pump or boiler. | always | no room has an estimate |
| Flow temperature | The averaged flow temperature the controller uses (`source`: your sensor). | flow sensor chosen | the sensor gives no plausible value |
| Return temperature | The averaged return temperature. | return sensor chosen | the sensor gives no value |
| Spread | Flow minus return, limited to 1–10 K; replaces the assumed 5 K. | flow and return sensor chosen | one of them has no value |
| Flow on the design day | The flow your heating reaches on the coldest design day, from the heating curve Thermogeist learns ([FAQ](faq/radiator_sizing.md)). Attributes: `slope_k_per_k`, `hours`, `outdoor_min_c`, `outdoor_max_c`, `confidence`. Diagnostic. | flow sensor chosen | fewer than 48 heating hours over at least 5 K of outdoor temperature learned, or no design outdoor temperature |
| Minimum valve opening, Dead band, Max. valve change per 30 min, Max. setback | Control settings, starting at the defaults of your heating type; attribute `source` is `profile` or `user` ([Getting started](getting-started.md#what-you-see-afterwards)). Configuration. | always | – |
| Window: close after, Window: resume heating after | House defaults for all rooms with window contacts, in seconds. Configuration. | always | – |
| Reset control settings to profile | Button: all control settings back to the defaults of the heating type. Configuration. | always | – |

## Room

| Entity | Meaning | When it exists | Unknown when |
|---|---|---|---|
| Climate (named like the room) | Room temperature and the setpoint you set (5–30 °C). Use it in dashboards and with voice assistants. | always | – (temperature unknown while the room sensor has no value) |
| Control | Switch: off = Thermogeist only observes, on = it writes to the thermostats. Attribute `can_control`. | always | unavailable while the room has no thermostat |
| Active reason | Why the room aims for its current target, with an [FAQ page](faq/README.md) per reason. Attributes: `severity`, `since`, `faq` and the reason's numbers. | always | – |
| Target temperature | What the room aims for right now, e.g. 7 °C while a window is open. | always | the room should not heat (central *Stop*) |
| Heat demand | Watts the room needs right now to hold its target: heat loss coefficient × (target − outdoor). | always | no heat load or design outdoor temperature on the house, or no outdoor temperature |
| Estimated radiator output | Watts the radiators give right now – put it next to *Heat demand* ([details below](#estimated-radiator-output)). Attributes: `max_output_w`, `radiators`, `valve_characteristic`, `missing`. | room has thermostats | see `missing`: a thermostat without rated output or valve position, no flow or room temperature |
| Share of heat load | The room's share, estimated or entered. Attributes: `source` (`estimated` / `known`), `scaled_down`. Diagnostic. | always | – |
| Heat loss coefficient | Watts per kelvin of difference to outside. Diagnostic. | always | no heat load or design outdoor temperature on the house |
| Heat from devices | Watts your devices release into the room, after factors, averaged over 10 minutes ([Rooms](rooms.md#devices-that-heat-the-room)). Attributes: `sources`, `factor_entities`. | heat sources chosen | – |
| Planned valve position | What Thermogeist would set (observe mode) or sets (control). Attributes: `feed_forward`, `feed_forward_missing`, `proportional`, `integral`, `limits` and the temperatures used ([Thermostats](thermostats.md#what-you-see)). | room has thermostats | right after start, before the first plan |
| Radiator size | Can the radiators hold the setpoint on the design day? Attributes with the numbers ([FAQ](faq/radiator_sizing.md)). Diagnostic. | room has thermostats | – (shows *not assessable yet* with `missing`) |
| Windows | On while a contact of the room is open. Attributes: `contacts`, `heating_paused`, `frost_guard`, `close_after_s`, `resume_after_s`. | window contacts chosen | – |
| Window: close after, Window: resume heating after | The room's own window times; house value until you change them (attribute `source`). Configuration. | window contacts chosen | – |
| Window: reset times to house | Button: the room follows the house's window times again. Configuration. | window contacts chosen | – |

## Thermostat

Named after the thermostat, on the room device.

| Entity | Meaning | When it exists | Unknown when |
|---|---|---|---|
| Kind *thermostat* | Valve-based or setpoint-based. Attributes: `strategy`, `profile`, `radiator_output_w`, `roles`, and what Thermogeist last wrote (`last_write`, `last_write_value`, `last_confirmation`, `rewrites_last_hour`; by setpoint `setpoint_offset`). Diagnostic. | always | – |
| Valve position *thermostat* | Where the valve really is – compare it with the planned one. `source: reported` when the thermostat reports it; `source: derived` for Sonoff thermostats: the set position while the thermostat heats, the minimum opening while it rests (`hvac_action`). | the role *Valve position (read)* is filled in, or a Sonoff with valve position (set) and minimum opening | the thermostat reports nothing, or a Sonoff reports neither heating nor resting |

## Estimated radiator output

Thermogeist estimates in two steps for each thermostat with a rated output:

1. **Fully open** (`max_output_w`): the rated output converted to the current temperatures,
   using the standard radiator formula (EN 442): rated output × ((flow − spread/2 − room) /
   49.8 K)^1.3. Without a return sensor the spread is assumed to be 5 K. This number is fairly
   reliable if the rated output is right.
2. **At the current valve position:** below 10 % practically no water flows. Above that, the
   output rises steeply, because a radiator with half the water flow still gives most of its
   heat. Thermogeist assumes: output = fully open × √((valve − 10 %) / 90 %). It uses the same
   curve, the other way round, to plan the valve. Your valve may behave differently, which is
   why `valve_characteristic` says `assumed`.

| Valve | Share of the full output |
|---|---|
| 10 % or less | 0 % |
| 20 % | 33 % |
| 40 % | 58 % |
| 55 % | 71 % |
| 75 % | 85 % |
| 100 % | 100 % |

Example: rated output 700 W, flow 40 °C, room 19.5 °C, no return sensor → fully open about
186 W. With the valve at 39 % the estimate is about 106 W.

**Which valve position:** the one the thermostat reports (`valve_source: reported`), for Sonoff thermostats the derived one (`derived`, see *Valve position*). If it
reports none and Thermogeist sets the valve itself, the planned position (`planned`). A
setpoint-based thermostat that reports no valve has no position Thermogeist could use: the
room's estimate is then unknown, but `max_output_w` still shows what the radiators could give.

**Reading it:** if the estimated output stays well below the heat demand while the valve is
fully open, the radiator is too small for the current flow – see *Radiator size*. If it is far
above the demand and the room still does not get warm, the rated output may be too high or the
radiator does not get enough water. Devices that heat the room (*Heat from devices*) are not
included: the radiator only has to make up the rest.
