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
| Window and door contacts | Optional. If one is open for 30 seconds, the room stops heating until it is closed ([FAQ](faq/window_open.md)). |
| Design indoor temperature | Planning value from the heat load calculation – not the temperature you heat to. Usually 20 °C, bathrooms 24 °C, heated halls 15 °C. A bathroom designed for 24 °C gets a larger share. |

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
| Share of heat load | The room's share, estimated or entered. |
| Heat loss coefficient | Watts per kelvin of temperature difference to outside. |

On the house you additionally see **Heat load not assigned to a room**.

To change a room, open the Thermogeist entry and click the gear icon (⚙) next to the room.


## Devices that heat the room (coming soon)

> Planned for a later version. This section explains in advance which factor to choose.

Many devices turn their power into heat in the room: a gaming PC at 300 W is a small radiator.
You will be able to give a room the power sensors (W) of such devices; Thermogeist then
subtracts their heat from what the radiator has to deliver. The power is averaged over
10 minutes, so a PC jumping between 80 and 400 W does not move the valve with every load change.

Per device a **factor** says how much of the power really stays in the room as heat.

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

Next: [assign thermostats](thermostats.md).
