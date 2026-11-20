# Getting started

**English** | [Deutsch](../de/getting-started.md)

> Thermogeist is in an early stage. Right now you can describe your house. Rooms and
> thermostats follow in the next versions.

## Install

**Manually from the zip**

1. Download `thermogeist.zip` from the latest release.
2. Unpack it into `config/custom_components/thermogeist/` on your Home Assistant.
3. Restart Home Assistant.

Installation through HACS will be described once Thermogeist is published.

## Describe your house

Go to **Settings → Devices & services → Add integration** and search for **Thermogeist**.

### Step 1: the three essentials

| Field | What to enter |
|---|---|
| Name | How the house should appear, e.g. "Home" or "Granny flat". |
| Heating type | Heat pump, boiler (gas, oil, pellets, district heating) or direct electric heating. This decides how calmly Thermogeist regulates. |
| Outdoor temperature sensor | Any sensor that measures the outdoor temperature, e.g. a weather station or your heat pump's outdoor sensor. |

### Step 2: details (optional)

Every field may stay empty. The more you fill in, the better Thermogeist starts.

| Field | What to enter |
|---|---|
| Heat load | The heat your house needs on the coldest design day, in kW. You find it in the heat load calculation from your heating installer or energy consultant. |
| Design outdoor temperature | The outdoor temperature the heat load was calculated for. Required if you enter a heat load. |
| Heated living area | Total heated floor area, without balconies and terraces. Thermogeist uses it to estimate each room's share of the heat load from the room's size – a 20 m² room in a 160 m² house starts at about 12.5 %. Recommended. |
| Share outside Thermogeist | Part of the heat load in rooms Thermogeist will not control, e.g. a bathroom with floor heating. Only needed if you know it from a heat load calculation; otherwise it follows from the living area. |

> **Tip: finding the design outdoor temperature.** It depends on where you live. Search the
> web for "design outdoor temperature" together with your postcode – in Germany for
> "Normaußentemperatur" and your postcode. If you have a heat load calculation, the value is
> written in it.

You can add more than one house, for example a granny flat with its own heating.

## What you see afterwards

Thermogeist creates a device for your house:

- **Central mode** – *Auto*, *Stop* or *Frost protection* for the whole house. The setting
  survives restarts.
- **Diagnostic values** – your heating type, heat load and design temperature, plus the
  defaults that follow from the heating type:

| Default | Heat pump | Boiler | Direct electric |
|---|---|---|---|
| Minimum valve opening | 40 % | 0 % | 0 % |
| Dead band above the setpoint | 0.5 K | 0.2 K | 0.2 K |
| Max. valve change per 30 min | 10 % | 30 % | 100 % |
| Max. setback | 2 K | 4 K | 4 K |

Why so different? A heat pump works best when water keeps flowing, so Thermogeist keeps
valves open and moves them slowly. A boiler can react faster and cope with valves that close.

## Changing your settings

Open the Thermogeist entry and choose **Configure**. You can change everything except the name;
Thermogeist reloads afterwards.
