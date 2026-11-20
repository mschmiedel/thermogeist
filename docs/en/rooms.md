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

To change a room, open it in the Thermogeist entry and choose **Reconfigure**.
