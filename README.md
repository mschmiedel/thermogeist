<p align="center"><img src="brand/logo.png" alt="Thermogeist" width="480"></p>

# Thermogeist

**English** | [Deutsch](README.de.md)

> **Status: alpha, in daily use.** Describe your house and rooms, add thermostats, watch what
> Thermogeist would do (observe mode) and switch control on room by room – by valve position or
> by setpoint. Expect changes between versions. Start with
> [Getting started](docs/en/getting-started.md).

Calm, understandable radiator control for Home Assistant – for the whole house, not just one
valve at a time.

## Why

Smart radiator valves usually act like isolated gadgets. They don't know your house, they react
nervously, and when they switch off you rarely learn why. Thermogeist adds the missing layer:

- **It knows your house and rooms.** Heat load, each room's share and the radiator size give a
  model of what every room needs – and Thermogeist learns from normal operation how much the
  room really needs.
- **Heat-pump friendly.** Valves keep a minimum opening and move slowly instead of slamming
  shut; a restart or a window never makes them jump.
- **Always explains itself.** Every reason – window, frost protection, a silent sensor – is
  visible in Home Assistant, with a help page.
- **Simple to set up.** A few questions instead of long forms; thermostats are recognised and
  added right when you add a room.

## What it does today

- **Room control** by valve position (Sonoff TRVZB, Bosch Radiator Thermostat II) or by
  setpoint (any thermostat with a climate entity), with a calm controller that plans ahead from
  the heat demand.
- **Windows:** heating pauses 30 s after a contact opens and resumes at once when it closes;
  thermostats' own window functions and schedules cannot change your room setpoints.
- **Learning:** each room learns from quiet hours how much of its modelled demand it really
  needs, by day and night.
- **Heat from devices:** a gaming PC or an air conditioner in heating mode counts, with a factor
  per device (also from a sensor, e.g. a COP template).
- **Diagnostics:** radiator size per room (too small, right, much larger than needed), estimated
  radiator output, the heat demand and supply of all rooms on the house, a heating curve learned from the flow sensor – or entered as two points
  when there is no sensor.
- **Child lock** per room: kept on after firmware updates and battery changes, adopted when
  you lock a thermostat at the device, 30 minutes off with one button.
- **Reliable with real devices:** settings that a firmware update resets are set again, a
  thermostat that lost its calibration is reported, silent sensors and stale values are recognised.

Planned: schedules, connections between rooms (open doors) – see [`spec/roadmap.md`](spec/roadmap.md).

## Supported devices

| Device | Connection | How | Tested |
|---|---|---|---|
| Sonoff TRVZB | Zigbee2MQTT | Valve position, room sensor sent to the thermostat | yes |
| Bosch Radiator Thermostat II (BTH-RA) | Zigbee2MQTT | Valve position | yes |
| Sonoff TRV-ZBT (Gen 2) | Zigbee2MQTT | Valve position | profile, not tested |
| Other Zigbee2MQTT thermostats | Zigbee2MQTT + MQTT integration | Roles detected from Zigbee2MQTT | detected, not tested |
| Any thermostat with a `climate` entity (e.g. Bosch Smart Home) | Home Assistant | Setpoint – with limits, see [Thermostats](docs/en/thermostats.md) | yes |

## Installation

**HACS (custom repository):** HACS → ⋮ → *Custom repositories* → add
`https://github.com/mschmiedel/thermogeist`, category *Integration*. While Thermogeist is in
alpha, enable *Show beta versions* for it. Then install, restart Home Assistant and add the
integration.

**Manually:** download `thermogeist.zip` from the latest
[release](https://github.com/mschmiedel/thermogeist/releases), unpack it into
`config/custom_components/thermogeist/` and restart Home Assistant.

Requires Home Assistant 2026.10 or newer.

## Documentation

- [Getting started](docs/en/getting-started.md) – install and describe your house
- [Rooms](docs/en/rooms.md) and [Thermostats](docs/en/thermostats.md) – with flow diagrams
- [All entities](docs/en/entities.md) – what each value means and when it is available
- [FAQ](docs/en/faq/README.md) – every reason a room can show

The product specification lives in [`spec/`](spec/).

## License

[MIT](LICENSE). See [CREDITS.md](CREDITS.md) for projects and sources this one builds on.
