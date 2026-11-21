# Thermostats

**English** | [Deutsch](../de/thermostats.md)

> **Observe first, then control.** New rooms start in observe mode: Thermogeist only shows
> what it would do. When you are happy with the plan, switch **Control** on for the room.

## Add a thermostat

Thermostats belong to their room. Open the Thermogeist entry of your house, click the gear
icon (⚙) next to the room and choose **Add thermostat**. A room can have several thermostats.

The same menu offers **Edit room**, **Edit thermostat** and **Remove thermostat**. To move a
thermostat to another room, remove it here and add it there; on removal it gets its own device
settings back.

### Step 1: device

| Field | What to enter |
|---|---|
| Thermostat | The thermostat device in Home Assistant (it must have a climate entity). |
| Radiator rated output | Optional. The radiator's output in W at 75/65/20 °C, from its data sheet or type plate. |

### Step 2: what does what?

Thermogeist recognises known models and pre-fills which entity does what. Check the list and
change anything that looks wrong; empty fields are simply not used. You can pick entities of
other devices too – some integrations (e.g. Bosch Smart Home) split climate and valve
position across separate devices.

To change a thermostat later: gear icon (⚙) next to its room → **Edit thermostat**.

| Role | Meaning |
|---|---|
| Climate entity | Required. The thermostat's own climate entity. |
| Valve position (read) | Only if the thermostat reports how far its valve really is open. Leave it empty for the Sonoff thermostats – Thermogeist works their position out itself (see below). Never choose the entity from *Valve position (set)*: it only echoes what Thermogeist wrote (the dialog refuses it; the Bosch BTH-RA is the exception the profile fills in itself). |
| Valve position (set) | Lets Thermogeist set the valve directly. Without it, the thermostat is controlled by its setpoint. |
| Minimum opening on the device | A fallback stored on the thermostat; it still works if Home Assistant is down. |
| External temperature input | Lets the thermostat use your room sensor instead of its own. |

Known models today:

| Model | Kind | Notes |
|---|---|---|
| Sonoff TRVZB | Valve-based | Firmware 1.1.4 or newer. Switch off *smart temperature control*. |
| Sonoff TRV-ZBT (Gen2) | Valve-based | Switch off *smart temperature control*. |
| Bosch Radiator Thermostat II (BTH-RA) | Valve-based | No minimum opening on the device. Keeps a written valve position for 15 minutes only; Thermogeist confirms it every 10 minutes. |

Every other thermostat works **setpoint-based**: Thermogeist tells it which temperature to aim
for, and the thermostat moves its valve itself.

### How to control

In the second step you choose **How to control**:

| Choice | What happens |
|---|---|
| Automatic (default) | By valve position if *Valve position (set)* is filled in, otherwise by setpoint. |
| By valve position | Thermogeist sets the valve itself: calm, with minimum opening and feed-forward. Needs *Valve position (set)*. |
| By setpoint | The thermostat regulates with its own controller; Thermogeist only sends the right target. Works with every thermostat, also with valve-based ones if you prefer it. |

**By setpoint, with external temperature input** (e.g. Bosch): Thermogeist sends the room
temperature to the thermostat and sets the room target as its setpoint. The thermostat then
regulates on the real room temperature.

**By setpoint, without external temperature input:** the thermostat measures next to the warm
radiator and would stop heating too early. Thermogeist compares its reading with the room sensor
(30-minute average) and adds the difference: room target 20 °C, thermostat 2.5 K warmer than the
room → setpoint 22.5 °C. The thermostat display therefore shows the corrected value. Setpoints
stay within 5–30 °C in 0.5 K steps.

Limits of *by setpoint*: no minimum opening and no calm valve movement – the thermostat's own
controller decides how far it opens.

> **Limit of control by setpoint: everything on the thermostat's display is ignored.**
> Turning the knob or pressing buttons on the thermostat does nothing lasting – Thermogeist puts
> its own value back within about a minute. Set the temperature in Home Assistant (the room's
> climate entity, dashboards, voice assistants). The reason: Thermogeist only sees the setpoint
> on the thermostat, not who changed it. A person at the knob, the thermostat's own schedule,
> its window function or its frost protection all look the same.
>
> Further limits: without an external temperature input the display shows a corrected value
> instead of your room setpoint, and the thermostat's own controller decides how far the valve
> opens. Rooms can therefore end up half a degree too warm. If your thermostat offers a valve
> position, control by valve is the calmer choice. Switch off the thermostat's own schedules
> and window detection.

## Control

Each room has a switch **Control**. Off (default): observe only. On: Thermogeist writes to the
room's thermostats – the valve position or the setpoint, depending on *How to control*.

What happens when you switch it on:

1. For 90 seconds after a Home Assistant restart nothing is written (*Waiting after restart*).
2. Device settings needed for control are applied – e.g. Bosch `operating_mode` → *manual*,
   Sonoff *smart temperature control* off. The previous values are remembered.
3. Every minute, by valve position: planned valve position, minimum opening (Sonoff), room
   temperature as external temperature, and the room target as the thermostat's setpoint, so its
   display stays honest.
4. By setpoint: room temperature as external temperature (if possible) and the setpoint – changes
   of at least 0.5 K, at most every 10 minutes. Window open or *Stop*: 5 °C at once.

What happens when you switch it off: all remembered device settings and the valve position are
put back; setpoint thermostats get the plain room setpoint. The thermostat regulates on its own
again.

**New or replaced thermostat:** when the thermostats of a room change – added, replaced, removed or edited – the room's control starts fresh from the heat demand. What it learned belongs to the old valves. This happens on its own.

**Turning the knob** on a thermostat controlled **by valve** sets the room setpoint (after
20 seconds without further turning). You see it in the logbook. On a thermostat controlled **by
setpoint** the knob is ignored (see the limit above).

**Window function of the thermostat:** some thermostats lower their setpoint themselves when a
window opens (to 8 °C, for example) and put it back on closing. That must not become your room
setpoint. So on a thermostat controlled by valve, while a window contact of the room is open
and for 2 minutes after closing, Thermogeist ignores setpoint changes on the thermostat and
afterwards writes its own value again. A knob turned in that time is ignored too – turn it again
later or set the room in Home Assistant. This works only if the window contact is also chosen in
the Thermogeist room.

**After the window:** once all contacts are closed (10 seconds by default), the valve goes
straight to the position needed now – no slow ramp-up, also with a heat pump. The same
happens after a restart or a silent room sensor: until the room temperature is known the
valve stays at the safe minimum opening, then it goes straight to the computed position. Thermostats
controlled by setpoint get 5 °C while the window is open; some (Bosch Smart Home) switch
themselves *off* at 5 °C. Thermogeist switches them back to *heat* and sends the setpoint
again.

**If a thermostat keeps changing its valve on its own**, Thermogeist writes again up to three
times per hour, then switches the room back to observe and shows a repair issue
([FAQ](faq/device_overrides_valve.md)).

Before you switch control on, retarget your own automations, dashboards and voice assistants
from the thermostat to the room's climate entity – otherwise two regulators fight.

### When the room is too warm

Two settings on the house decide what happens when a room gets warmer than its target: the
**dead band** (heat pump: 0.5 K) and the **minimum valve opening** (heat pump: 40 %, you may have
changed it). Example: target 19.5 °C, dead band 0.5 K, minimum opening 30 %.

| Room | What Thermogeist does | Limits you may see |
|---|---|---|
| below 19.5 °C | Regulates normally: feed-forward plus reaction to the difference. The valve may open, slowly. | – |
| 19.5–20.0 °C (inside the dead band) | A little too warm, still fine. The quick reaction ignores it; the valve is not opened further and may close, but not below 30 %. | `hold_when_warm`, `min_opening` |
| 20.0–20.5 °C | As before, but now the quick reaction also pulls down. Still not below 30 %. | `hold_when_warm`, `min_opening` |
| above 20.5 °C (dead band + 0.5 K) | **Comfort comes first:** the minimum opening no longer applies. The valve may close below 30 %, slowly, towards what the calculation says. | `min_opening_relaxed` |
| back below 20.0 °C | Only now does the minimum opening apply again. In between the previous state stays, so it does not switch on and off with every tenth of a degree. | `min_opening` |

**Why:** a heat pump works most efficiently when water flows through every radiator. Thermogeist
therefore accepts half a degree too much rather than closing a valve. Only when it gets
noticeably too warm does comfort win. A room that often shows `min_opening_relaxed` has a
radiator that is too big for it at the minimum opening.

Sonoff thermostats rest on their stored minimum opening (*closing degree*) while the room is
warmer than its setpoint. Whenever the planned position is below the minimum opening,
Thermogeist lowers that stored value along with it, and puts it back to the minimum opening once
the plan is there again. Sun or a gaming PC therefore no longer keep the valve at the minimum.

**A room that stays too warm teaches the control.** While a room is above its target, the slow
correction keeps lowering the planned position, even when the room is far above it. A lasting
overshoot means the calculation asks for too much – because of sun, devices or a heat demand
that is set too high – and the room should not have to swing back first before that is learned.

With a boiler the dead band is 0.2 K and the minimum opening 0 %, so this stage practically never
applies.

## Flow temperature (optional)

On the house (**Configure**) you can choose a **flow temperature sensor** – the temperature of
the water going to the radiators, e.g. from your heat pump. Together with the radiator outputs
and the house heat load, Thermogeist then calculates a good starting valve position instead of
finding it slowly.

Optionally also a **return temperature sensor** – the water coming back, measured at the same
place (e.g. heating circuit return). Without it Thermogeist assumes the radiators are 2.5 K
cooler than the flow on average (5 K spread). With it the measured spread is used (30-minute
average, limited to 1–10 K). With a large spread the radiators are cooler, and the valves open a
bit further. The house return mixes all radiators, so it tells the average, not one radiator.
Calibrate strap-on return sensors the same way as the flow sensor.

## Choosing the flow temperature sensor

The flow temperature is the most sensitive input of the feed-forward. At heat-pump temperatures
there are only a few kelvin between water and room, so **1 K measurement error changes the
calculated radiator output by 20–30 %**. Choose and check the sensor carefully.

**Where to measure**

| Sensor | Suitable? | Why |
|---|---|---|
| Heating circuit flow, after the buffer tank (where the radiators get their water) | **yes – recommended** | Shows what the radiators really get. During hot-water charging it drops slowly; Thermogeist then opens the valves a little – the right compensation. |
| Heat pump's own flow sensor (outlet of the heat pump) | **only with care** | During hot-water charging it shows 45–50 °C. Thermogeist would think the radiators are hot and close the valves, although they get cooler. With a buffer tank the heat pump's flow is also not what reaches the radiators. |
| Boiler flow without buffer | yes | Same water as the radiators. |

If you have no heating-circuit sensor and must use the heat pump's sensor: watch the planned
valve position during hot-water charging. A future version can hold the value during hot water
and defrost if you give it the heat pump's operating mode.

**Strap-on sensors: calibrate them**

Sensors strapped onto the pipe – even under insulation – often read **2–4 K too low**, because
they also feel the cooler surroundings. To find the offset without dismantling anything:

1. Wait for a time when the heat pump stands still (no heating, no hot water, no defrost) while
   the heating circuit pump keeps running – at night or on a mild afternoon, 30–60 minutes.
2. Then water in the buffer, the heat pump and the heating circuit flow has almost the same
   temperature. Compare your sensor with the heat pump's or the buffer's sensor.
3. Enter the difference as an offset for your sensor in Home Assistant.

Example from a real installation: heat pump flow 28.9 °C, heat pump return 28.2 °C, buffer
28.5 °C, heating-circuit strap-on sensor 25.6 °C → offset about +3 K.

**No sensor at all?** Thermogeist still works: without the feed-forward it finds the right valve
position through slow correction, which takes about a day instead of hours. The planned valve
position then shows `feed_forward_missing: flow_temperature`.

## What you see

On each room:

| Entity | Meaning |
|---|---|
| Planned valve position | What Thermogeist would set right now. Attributes show the parts: *feed_forward* (from the heat demand), *proportional* (reaction to the temperature difference), *integral* (slow correction), and *limits* that applied. If *feed_forward* is empty, *feed_forward_missing* tells you what is missing – usually the flow temperature sensor on the house or the radiator output. |
| Valve position *thermostat* | The actual valve position. Put it next to the planned one in a history graph. Attribute `source`: `reported` (the thermostat reports it) or `derived` (Sonoff: the thermostat moves between two positions with its own controller – the position Thermogeist set while it heats, the minimum opening while it rests; `hvac_action` shows which). |
| Kind *thermostat* | Valve-based or setpoint-based, with *strategy* (your choice), profile and roles as attributes. |

### Limits you may see

| Limit | Meaning |
|---|---|
| `min_opening` | The valve stays at the minimum opening of your heating type (heat pump: 40 %). |
| `min_opening_relaxed` | The room is more than the dead band + 0.5 K above its target, so the valve may close below the minimum opening ([when the room is too warm](#when-the-room-is-too-warm)). Typical for radiators that are too big for the room. |
| `hold_when_warm` | The room is above its target, so the valve is not opened further, whatever the calculation says. |
| `rate_limit` | The valve moves slowly on purpose (heat pump: max. 10 % per 30 minutes). |
| `saturated` | The valve is fully open or at its lowest allowed position. |
| `stopped` | Central mode *Stop*: 0 %. |
| `safety` | The room sensor is silent: the valve goes to the minimum opening, at least 20 %. |

Each thermostat's *Kind* sensor shows what Thermogeist did with it: `last_write` and `last_write_value`, `last_confirmation`, `rewrites_last_hour` and `valve_refresh_minutes`. By setpoint: `last_write`, `last_write_value` (the setpoint sent) and `setpoint_offset` (the correction added to the room target).

The planned valve position also shows `flow_temperature_used`, `return_temperature_used` and `spread_used`.

**Confirm valve position every … minutes** (in the thermostat's settings): some thermostats drop a valve position set from outside after a while – the Bosch Radiator Thermostat II after 15 minutes. Thermogeist then resends the unchanged value at this interval (a radio message, no motor movement). Pre-filled from the device profile (Bosch: 10), empty = off.
