# Rooms

**English** | [Deutsch](../de/rooms.md)

> Rooms do not control thermostats yet. They show what each room needs and why – the basis for
> the next versions.

## Add a room

Open the Thermogeist entry of your house and choose **Add room**.

### Step 1: basics

| Field | What to enter |
|---|---|
| Name | e.g. "Living room". |
| Area | Optional. The room device is placed in this Home Assistant area. |
| Room temperature sensor | A sensor in the room, ideally away from the radiator and out of direct sunlight. |
| Share of the heat load | *Estimate from size and position* (most people) or *I know the share* (if you have a room-by-room heat load calculation). |
| Window and door contacts | Optional. If one is open for 30 seconds, the room stops heating until all are closed for 10 seconds; both times can be changed ([FAQ](faq/window_open.md)). |
| Design indoor temperature | Planning value from the heat load calculation – not the temperature you heat to. Usually 20 °C, bathrooms 24 °C, heated halls 15 °C. A bathroom designed for 24 °C gets a larger share. |
| Devices that heat the room | Optional. Power sensors (W) of devices in the room, see [below](#devices-that-heat-the-room). |

### Step 2a: size and position (estimate)

Rough values are fine – Thermogeist will learn the real behaviour later.

| Field | What to enter |
|---|---|
| Floor area | In m². Galleries and open spaces count their floor area once. |
| Ceiling height | With a sloped ceiling: the highest point. |
| Lowest point under a sloped ceiling | Only for sloped ceilings. Thermogeist uses the mean of lowest and highest point. |
| Exterior walls | Walls that face outside. A corner room usually has 2, a hallway inside the house 0. |
| Above / below the room | Heated room, unheated room (attic, basement), roof or ground. |

**How the estimate works:** a typical room – 2.5 m high, two exterior walls, heated rooms above
and below – gets exactly its share of the living area: 20 m² in a 160 m² house = 12.5 %.
Higher ceilings, more exterior walls, a roof or the ground below increase the share; interior
rooms and low sloped rooms get less.

### Step 2b: known share

Enter the room heat load divided by the house heat load, in percent. Together with the other
rooms and the share outside Thermogeist it may not exceed 100 %.

**Hallways, corridors, stairwells:** leave them out if they have no thermostat – their part then
appears as "heat load not assigned to a room" on the house. With a thermostat, add them as a
normal room; few exterior walls give them a small share.

## What you see per room

| Entity | Meaning |
|---|---|
| Climate (named like the room) | Room temperature and the target temperature you set (5–30 °C). Use this in dashboards and with voice assistants. |
| Active reason | Why the room aims for its current target. Every reason has an [FAQ page](faq/README.md). |
| Target temperature | What the room actually aims for right now – e.g. 7 °C during frost protection. |
| Heat demand | Watts the room needs right now to hold its target (needs a heat load on the house). |
| Estimated radiator output | Only with thermostats: watts the radiators give right now, from rated output, flow, room temperature and valve position – compare it with the heat demand ([how it is estimated](entities.md#estimated-radiator-output)). |
| Share of heat load | The room's share, estimated or entered. |
| Heat loss coefficient | Watts per kelvin of temperature difference to outside. |
| Windows | Only with window contacts: on while one is open. Attributes: the contacts, `heating_paused`, `frost_guard`, and the times in use. In **Configuration**: *Window: close after*, *Window: resume heating after* (house value until you change it, attribute `source`) and *Window: reset times to house*. |
| Radiator size | Only with thermostats: can the radiators hold the setpoint on the coldest design day? *Much larger than needed*, *right size*, *just enough*, *too small* or *not assessable yet*, with the numbers as attributes ([FAQ](faq/radiator_sizing.md)). |
| Learned demand | Only with thermostats: how much of the expected heat the room really needs, learned from quiet hours; used to plan the valve ([FAQ](faq/learned_demand.md)). |
| Heat from devices | Only with heat sources: watts the devices release into the room (after factors, 10-minute average). Attributes: the factor in use per device and the factor sensors. |

On the house you additionally see **Heat load not assigned to a room** and **Room coverage**:
how much of the heat load your rooms (and the share outside Thermogeist) cover, with the missing
share and the living area not yet in any room as attributes. **Heat demand of rooms**, **Estimated
radiator output of rooms** and **Heat from devices of rooms** add up the rooms' values in
watts – what your rooms need and get right now – unlike the **Heat
load**, the fixed planning value for the coldest day. With flow and return sensors the
house also shows **Flow temperature**, **Return temperature** and **Spread** – the averaged
values the controller uses – and **Flow on the design day**, from the heating curve Thermogeist
learns ([FAQ](faq/radiator_sizing.md)).

All entities with their meaning and availability: [All entities](entities.md).

To change a room, open the Thermogeist entry, click the gear icon (⚙) next to the room and choose
**Edit room**. The same menu adds, edits and removes the room's thermostats.


## Devices that heat the room

Many devices turn their power into heat in the room: a gaming PC at 300 W is a small radiator.
Choose their power sensors (W) in the room's first step; Thermogeist then subtracts their heat
from what the radiator has to deliver. When a device switches off, the radiator takes over within
minutes. The planned valve position shows `heat_from_devices_w` and
`demand_covered_by_devices_pct`. The power is averaged over
10 minutes, so a PC jumping between 80 and 400 W does not move the valve with every load change.

In an extra step you set per device a **factor**: how much of the power really stays in the room
as heat.

**100 % – everything stays in the room** (default)

| Device | Why |
|---|---|
| PC, gaming PC, laptop, server, NAS, network gear | Electronics turn all power into heat. |
| TV, monitor, games console, audio | Same. |
| Lights | Practically all, also the light itself ends as heat. |
| Fridge, freezer | The heat comes out at the back – into the room. |
| Heat pump tumble dryer | Works with closed air, the heat stays in the room. |
| Hair dryer, fan heater, electric towel rail, infrared panel | Heat is what they are for. |
| Aquarium (heater, pump, light) | The water passes the heat on to the room. |

**Less than 100 % – part of the heat leaves the room**

| Device | Factor about | Why |
|---|---|---|
| Vented tumble dryer | 10–20 % | Warm, humid air is blown outside. |
| Washing machine | 10–20 % | The power mainly heats water, which goes down the drain. |
| Dishwasher | 20–40 % | Like the washing machine; the drying phase releases a little heat. |
| Cooker with an extractor hood venting outside | about 50 % | Part of the heat leaves with the exhaust air. |
| Instantaneous water heater, boiler | almost 0 % | The hot water leaves through the drain. |
| Smart plug feeding a power strip whose devices are elsewhere | the share that is in the room | The sensor measures more than arrives in the room. |
| PoE switch powering outdoor cameras | the switch's own share | The cameras use the rest outside. |

**More than 100 %:** a compressor dehumidifier releases its power plus the heat of the
condensed moisture – roughly 150 %. Choose 100 % anyway: assuming too little heat is harmless,
the slow correction makes up for it.

**Air conditioner that heats (air-to-air heat pump):** it takes heat from outside and releases
its power times its **COP** into the room, typically 3 to 4 times. The factor is then
COP × 100 %, up to 500 % is allowed. You rarely know the COP, but the EU energy label shows the
**SCOP** for heating (average heating season). Choose a little less, e.g. 400 % for a SCOP of 4.6
– on cold days the COP is lower. When the unit cools it is no heater: a template as power sensor
that reports 0 W in cooling mode keeps it from counting.

**Factor from a sensor:** optionally choose per device, next to the number, a *factor sensor* in
%. While it is available it wins; if it fails, the number applies again. Thermogeist limits it to
0–500 %. This lets a template make the COP follow the outdoor temperature. A rough estimate for
split air conditioners: `COP = 0.45 · T_hot / (T_hot − T_cold)` in kelvin, with `T_hot` = room +
15 K and `T_cold` = outside − 6 K. That gives about 4.2 at 9 °C outside and 2.6 at −10 °C. The
entity ids in the example are placeholders:

```yaml
template:
  - sensor:
      - name: "Living room air conditioner factor"
        unit_of_measurement: "%"
        state: >
          {% set room = states('sensor.living_room_temperature') | float(21) %}
          {% set outside = states('sensor.outdoor_temperature') | float(5) %}
          {% set hot = room + 15 + 273.15 %}
          {% set cold = outside - 6 + 273.15 %}
          {% set cop = 0.45 * hot / (hot - cold) %}
          {{ (([1, cop, 5] | sort)[1] * 100) | round(0) }}
```

The **Heat from devices** sensor shows the factor in use in its `sources` attribute and the
chosen factor sensors in `factor_entities`.

Next: [assign thermostats](thermostats.md).
