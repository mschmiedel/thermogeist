<p align="center"><img src="brand/logo-light.svg" alt="Thermogeist" width="480"></p>

# Thermogeist

**English** | [Deutsch](README.de.md)

> **Status: early development.** You can describe your house; rooms and thermostats follow.
> Start with [Getting started](docs/en/getting-started.md).

Calm, understandable radiator control for Home Assistant – for the whole house, not just one
valve at a time.

## Why

Smart radiator valves usually act like isolated gadgets. They don't know your house, they react
nervously, and when they switch off you rarely learn why. This integration adds the missing layer:

- **One place for the whole house.** Heating type, schedules, window rules and groups are set once
  and inherited by every room.
- **It knows your rooms.** Give it your house's heat load and each room's share, optionally the
  radiator size. It uses this to regulate smoothly and to tell you if a radiator is too big or too
  small.
- **Heat-pump friendly.** A dedicated heat-pump mode keeps valves open and moves them gently
  instead of slamming them shut.
- **Always explains itself.** Every throttle, shutdown or override comes with a plain-language
  reason you can see in Home Assistant.
- **Shows whether it is still learning.** No more guessing if your thermostat has settled in.

## Supported devices (planned)

| Device | Connection | Notes |
|---|---|---|
| Sonoff TRVZB | Zigbee2MQTT | Primary target, direct valve control |
| Bosch Radiator Thermostat II | Zigbee2MQTT | Direct valve control, no device-side minimum opening |
| Any `climate` entity | Home Assistant | Basic support via setpoint control |

## Documentation

User documentation lives in [`docs/en/`](docs/en/). The product specification lives in
[`spec/`](spec/).

## License

[MIT](LICENSE). See [CREDITS.md](CREDITS.md) for projects that inspired this one.
