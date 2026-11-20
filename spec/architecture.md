# Architecture

## Layers

```
Home Assistant (entities, config flow, logbook, repairs)
        │  thin translation layer
        ▼
Core (plain Python, no HA imports)
  ├─ House model     house → group → room → actuator, with inheritance
  ├─ Rules           window, schedule, away, overrides
  ├─ Controller      feed-forward + feedback → heat demand 0–100 %
  ├─ Limiters        frost protection, over-temperature, sensor failure
  ├─ Learning        room parameters, opening point, learning state
  ├─ Diagnostics     radiator sizing, balancing
  └─ Decisions       every change as a Decision with a reason code
        │
        ▼
Actuator adapters (per device type, capability model)
        │
        ▼
Device (TRV via Zigbee2MQTT / climate entity)
```

## Requirements

| ID | Requirement | Status |
|---|---|---|
| ARC-001 | The core imports nothing from `homeassistant` and is testable without HA. | implemented |
| ARC-002 | The core gets time exclusively through `TimeProvider`. | implemented |
| ARC-003 | Every change to an actuator passes through one central decision point and produces a Decision with a reason code. In M2 the decision covers the room's target temperature. | implemented |
| ARC-004 | The controller always outputs a device-independent heat demand (0–100 %). The adapter decides how to apply it. | implemented |
| ARC-005 | Settings are inherited house → group → room and can be overridden at every level. The effective source of each value is visible. | planned |

## Directories

| Path | Content |
|---|---|
| `custom_components/thermogeist/` | HA integration (domain `thermogeist`) |
| `custom_components/thermogeist/core/` | Core, no HA |
| `tests/` | Tests, structure mirrors the core |
| `tests/scenarios/` | Documented test scenarios per feature |
| `docs/en/`, `docs/de/` | User documentation |
| `spec/` | This specification |
