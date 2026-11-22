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
| Heat load | The heat load you entered, in kW: what the house needs on the coldest design day. A fixed planning value, not what is needed right now (see *Heat demand of rooms* below). Diagnostic. | always | no heat load entered |
| Design outdoor temperature | The outdoor temperature the heat load was calculated for. Diagnostic. | always | not entered |
| Share outside Thermogeist | Part of the heat load in rooms Thermogeist does not control, as entered. Diagnostic. | always | – |
| Heat load not assigned to a room | Part of the heat load no room (and no share outside) covers yet. Diagnostic. | always | – |
| Room coverage | 100 % minus the part not assigned. Attributes: `missing_pct`, `floor_area_not_in_rooms_m2`, `rooms`. | always | – |
| Heat demand of rooms | Watts your rooms need right now to hold their targets – the sum of their *Heat demand*. | always | no heat load on the house |
| Estimated radiator output of rooms | Watts all radiators give right now – the sum of the rooms' *Estimated radiator output*. Only radiators: compare it over time with what your heat pump or boiler delivers (a heat meter). | always | no room has an estimate |
| Heat from devices of rooms | Watts your devices release into the rooms – the sum of the rooms' *Heat from devices*. Kept apart because this heat comes from the socket, not from the heating. | always | no room has an estimate |

The three sums cover the same rooms, so you can compare them directly. A room whose radiators cannot be estimated (no valve position, or no thermostat) is left out of all three and named in the attribute `rooms_without_estimate`; `rooms` says how many are counted. Only rooms in Thermogeist count (see *Room coverage*). There is no combined sum of radiators and devices; a template can add both if you need it.

| Entity | Meaning | When it exists | Unknown when |
|---|---|---|---|
| Flow temperature | The averaged flow temperature the controller uses (`source`: your sensor, or `heating_curve` when it comes from the heating curve at the current outdoor temperature). | flow sensor or heating curve entered | the sensor gives no plausible value |
| Return temperature | The averaged return temperature. | return sensor chosen | the sensor gives no value |
| Spread | Flow minus return, limited to 1–10 K; replaces the assumed 5 K. | flow and return sensor chosen | one of them has no value |
| Flow on the design day | The flow your heating reaches on the coldest design day, from the heating curve Thermogeist learns ([FAQ](faq/radiator_sizing.md)). Attributes: `slope_k_per_k`, `hours`, `outdoor_min_c`, `outdoor_max_c`, `confidence`. With an entered heating curve it comes from that curve (`source`: `heating_curve` and the two points). Diagnostic. | flow sensor or heating curve entered | fewer than 48 heating hours over at least 5 K of outdoor temperature learned, or no design outdoor temperature |
| Minimum valve opening | How far a valve stays open at least while controlled, in %. Heat pump 40 %: water should always be able to flow through the radiators, otherwise the heat pump keeps switching on and off. Only when a room is clearly too warm (more than dead band + 0.5 K above its target) may the valve go below ([When the room is too warm](thermostats.md#when-the-room-is-too-warm)). Boiler and electric: 0 %. Configuration. | always | – |
| Dead band | How much warmer than its target a room may get before the controller closes the valve because of it, in K. Example heat pump 0.5 K, target 21 °C: up to 21.5 °C the valve stays calm – a bit of sun or cooking leaves it alone. If the room stays too warm for long, the slow correction still takes the valve back step by step. There is no dead band below the target: when it is too cold, the controller reacts at once. Configuration. | always | – |
| Max. valve change per 30 min | How far a valve moves at most within 30 minutes, in percentage points. Heat pump 10: from 40 % to 70 % takes at least an hour and a half. So the water flow changes only slowly and the heat pump runs evenly. Exceptions: after a window closes or a safety shutdown ends the valve goes straight back to the plan, and a room that is too warm is never opened further. Configuration. | always | – |
| Max. setback | For schedules and *Away*: how many kelvin cooler a room may get at most. Heat pump 2 K, because a deep setback costs more to heat up again than it saves. **No effect yet** – schedules are planned. Configuration. | always | – |
| Window: close after, Window: resume heating after | House defaults for all rooms with window contacts, in seconds. Configuration. | always | – |
| Reset control settings to profile | Button: all control settings back to the defaults of the heating type. Configuration. | always | – |

The four control settings apply to all rooms of the house and start at the defaults of your
heating type ([table](getting-started.md#what-you-see-afterwards)). The attribute `source` shows
`profile` (default) or `user` (changed by you). Usually there is nothing to change.

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
| Planned valve position | What Thermogeist would set (observe mode) or sets (control). Attributes: `mode` (`observe` / `control`), `feed_forward`, `feed_forward_missing`, `proportional`, `integral`, `limits` and the temperatures used ([Thermostats](thermostats.md#what-you-see)). | room has thermostats | right after start, before the first plan |
| Radiator size | Can the radiators hold the setpoint on the design day? Attributes with the numbers ([FAQ](faq/radiator_sizing.md)). Diagnostic. | room has thermostats | – (shows *not assessable yet* with `missing`) |
| Learned demand | How much of the heat its inputs suggest the room really needs, learned from quiet hours ([FAQ](faq/learned_demand.md)). Used to plan the valve once `settled`. Attributes: `state`, `quiet_hours`, `days`, `day_pct`, `night_pct`, `spread_pct`. | room has thermostats | still `learning` (fewer than 24 quiet hours on 3 days) |
| Child lock | Switch: on keeps the child lock of the room's thermostats on, also after a firmware update or battery change; off unlocks them. Locking a thermostat at the device switches it on. Works in observe mode too. Shows off during *off for 30 min* ([Thermostats](thermostats.md#child-lock)). | a thermostat of the room has a child lock | unavailable while no thermostat reports its lock |
| Child lock: off for 30 min | Button: unlocks the room's thermostats for 30 minutes, e.g. for a battery change; then the lock goes on again by itself. | as *Child lock* | unavailable while the child lock is off for good |
| Child lock back on | When the lock goes on again, shown as e.g. "in 27 minutes". Put it on your dashboard next to the switch. | as *Child lock* | outside the 30 minutes |
| Learning: start again | Button: the room forgets what it learned and starts again. Configuration. | room has thermostats | – |
| Windows | On while a contact of the room is open. Attributes: `contacts`, `heating_paused`, `frost_guard`, `close_after_s`, `resume_after_s`. | window contacts chosen | – |
| Window: close after, Window: resume heating after | The room's own window times; house value until you change them (attribute `source`). Configuration. | window contacts chosen | – |
| Window: reset times to house | Button: the room follows the house's window times again. Configuration. | window contacts chosen | – |

## Thermostat

Named after the thermostat, on the room device.

| Entity | Meaning | When it exists | Unknown when |
|---|---|---|---|
| Kind *thermostat* | Valve-based or setpoint-based. Attributes: `strategy`, `profile`, `radiator_output_w`, `roles`, and what Thermogeist last wrote (`last_write`, `last_write_value`, `last_confirmation`, `rewrites_last_hour`; by setpoint `setpoint_offset`). Diagnostic. | always | – |
| Valve position *thermostat* | Where the valve really is – compare it with the planned one ([why they can differ](thermostats.md#planned-and-actual-valve-position)). `source: reported` when the thermostat reports it; `source: derived` for Sonoff thermostats: the set position while the thermostat heats, the minimum opening while it rests (`hvac_action`). | the role *Valve position (read)* is filled in, or a Sonoff with valve position (set) and minimum opening | the thermostat reports nothing, or a Sonoff reports neither heating nor resting |

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
