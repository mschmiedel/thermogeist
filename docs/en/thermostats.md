# Thermostats

**English** | [Deutsch](../de/thermostats.md)

> **Observe first, then control.** New rooms start in observe mode: Thermogeist only shows
> what it would do. When you are happy with the plan, switch **Control** on for the room.

## Add a thermostat

Open the Thermogeist entry of your house and choose **Add thermostat**. You need at least one
room first.

### Step 1: room and device

| Field | What to enter |
|---|---|
| Room | The room this thermostat heats. A room can have several thermostats. |
| Thermostat | The thermostat device in Home Assistant (it must have a climate entity). |
| Radiator rated output | Optional. The radiator's output in W at 75/65/20 °C, from its data sheet or type plate. |

### Step 2: what does what?

Thermogeist recognises known models and pre-fills which entity does what. Check the list and
change anything that looks wrong; empty fields are simply not used. You can pick entities of
other devices too – some integrations (e.g. Bosch Smart Home) split climate and valve
position across separate devices.

To change a thermostat later, open the Thermogeist entry, find the thermostat below the house
and click its gear icon (⚙).

| Role | Meaning |
|---|---|
| Climate entity | Required. The thermostat's own climate entity. |
| Valve position (read) | Shows how far the valve is open – needed for the comparison. |
| Valve position (set) | Lets Thermogeist set the valve directly. Without it, the thermostat is controlled by its setpoint. |
| Minimum opening on the device | A fallback stored on the thermostat; it still works if Home Assistant is down. |
| External temperature input | Lets the thermostat use your room sensor instead of its own. |

Known models today:

| Model | Kind | Notes |
|---|---|---|
| Sonoff TRVZB | Valve-based | Firmware 1.1.4 or newer. Switch off *smart temperature control*. |
| Sonoff TRV-ZBT (Gen2) | Valve-based | Switch off *smart temperature control*. |
| Bosch Radiator Thermostat II (BTH-RA) | Valve-based | No minimum opening on the device. Whether it holds a written valve position is still being tested. |

Every other thermostat works **setpoint-based**: Thermogeist controls it through the target
temperature (from the next version on).

## Control

Each room has a switch **Control**. Off (default): observe only. On: Thermogeist writes to the
room's valve-based thermostats.

What happens when you switch it on:

1. For 90 seconds after a Home Assistant restart nothing is written (*Waiting after restart*).
2. Device settings needed for control are applied – e.g. Bosch `operating_mode` → *manual*,
   Sonoff *smart temperature control* off. The previous values are remembered.
3. Every minute: planned valve position, minimum opening (Sonoff), room temperature as external
   temperature, and the room target as the thermostat's setpoint, so its display stays honest.

What happens when you switch it off: all remembered device settings and the valve position are
put back. The thermostat regulates on its own again.

**Turning the knob** on a controlled thermostat sets the room setpoint (after 20 seconds without
further turning). You see it in the logbook.

**If a thermostat keeps changing its valve on its own**, Thermogeist writes again up to three
times per hour, then switches the room back to observe and shows a repair issue
([FAQ](faq/device_overrides_valve.md)).

Rooms with only setpoint-based thermostats cannot be controlled yet.

Before you switch control on, retarget your own automations, dashboards and voice assistants
from the thermostat to the room's climate entity – otherwise two regulators fight.

## Flow temperature (optional)

On the house (**Configure**) you can choose a **flow temperature sensor** – the temperature of
the water going to the radiators, e.g. from your heat pump. Together with the radiator outputs
and the house heat load, Thermogeist then calculates a good starting valve position instead of
finding it slowly.

## What you see

On each room:

| Entity | Meaning |
|---|---|
| Planned valve position | What Thermogeist would set right now. Attributes show the parts: *feed_forward* (from the heat demand), *proportional* (reaction to the temperature difference), *integral* (slow correction), and *limits* that applied. If *feed_forward* is empty, *feed_forward_missing* tells you what is missing – usually the flow temperature sensor on the house or the radiator output. |
| Valve position *thermostat* | The actual valve position, if the thermostat reports it. Put it next to the planned one in a history graph. |
| Kind *thermostat* | Valve-based or setpoint-based, with profile and roles as attributes. |

### Limits you may see

| Limit | Meaning |
|---|---|
| `min_opening` | The valve stays at the minimum opening of your heating type (heat pump: 40 %). |
| `min_opening_relaxed` | The room is clearly too warm, so the valve may close below the minimum opening. Typical for radiators that are too big for the room. |
| `rate_limit` | The valve moves slowly on purpose (heat pump: max. 10 % per 30 minutes). |
| `saturated` | The valve is fully open or at its lowest allowed position. |
| `stopped` | Central mode *Stop*: 0 %. |
| `safety` | The room sensor is silent: the valve goes to the minimum opening, at least 20 %. |
