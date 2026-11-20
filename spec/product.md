# Product

## Problem

Radiator thermostats are standalone devices. They know neither the house nor the room, often
regulate nervously, and when they throttle or switch off, the user rarely learns why. Whether a
thermostat is still learning or has settled stays unclear.

## Vision

A Home Assistant integration that adds a **house level** on top of the thermostats:
regulate calmly, understand the house, always explain itself.

## Audience

Home Assistant users with smart radiator thermostats (Zigbee), from beginners to tinkerers.
Beginners get a good result with a few inputs. Tinkerers can trace every decision.

## Differentiators

| ID | Feature | Status |
|---|---|---|
| PRD-001 | Heat-pump mode: keep valves open, regulate gently and slowly | planned |
| PRD-002 | Room knowledge from heat load, room share and radiator | planned |
| PRD-003 | Every decision with a readable reason (reason codes) | planned |
| PRD-004 | Visible learning state per room | planned |
| PRD-005 | Diagnostics: radiator too big / right / too small, with FAQ | planned |
| PRD-006 | House level with inheritance: heating type, rules, schedules, groups | planned |
| PRD-007 | Empirical, staged hydraulic balancing | planned |

## Out of scope

- **No control of the heat generator.** Flow temperature, heating curve and heat pump are a
  separate topic. The integration reads flow temperature or heating-curve values as input at
  most, and may expose figures such as the average valve opening.
- **No own Zigbee stack.** Devices are addressed through existing HA entities (Zigbee2MQTT, ZHA,
  native `climate` entities).
- **No cloud.** Everything runs locally.

## Quality goals

1. Easy to use: sensible defaults, setup through the HA UI.
2. Traceable: no intervention without a visible reason.
3. Robust: an outage of HA or a sensor leads to safe device behaviour.
4. Well tested: learning and control behaviour reproducible in simulated time.
