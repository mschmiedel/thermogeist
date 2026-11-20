# Specification

This folder describes the **current state** of the product: what it does, what is planned and
what deliberately is not. One file per feature. Change history lives in Git, not here.

## Status markers

Every requirement carries a status:

| Status | Meaning |
|---|---|
| `planned` | decided, not built yet |
| `in progress` | being built |
| `implemented` | code and tests exist, test scenario documented |
| `rejected` | deliberately not, with a reason |

Requirements have IDs of the form `<PREFIX>-<NO>`, e.g. `CTL-003`. Tests and test scenarios
refer to these IDs.

## Features

| File | Prefix | Content |
|---|---|---|
| [roadmap.md](roadmap.md) | — | Milestones, order of delivery |
| [product.md](product.md) | PRD | Vision, audience, scope |
| [architecture.md](architecture.md) | ARC | Layers, data flow, core without HA |
| [ha-integration.md](ha-integration.md) | HAI | Setup flow, devices, entities |
| [house-and-room-model.md](house-and-room-model.md) | MDL | Heating type, heat load, rooms, radiators |
| [controller.md](controller.md) | CTL | Feed-forward, feedback, limiters, profiles |
| [actuators.md](actuators.md) | ACT | Adapters, capability model, devices |
| [calibration.md](calibration.md) | CAL | Calibration mode with pipe sensor |
| [learning.md](learning.md) | LRN | Learning and visible learning state |
| [diagnostics.md](diagnostics.md) | DIA | Radiator sizing, hydraulic balancing |
| [decisions-and-reasons.md](decisions-and-reasons.md) | RSN | Reason codes, logbook, repairs |
| [operation-and-overrides.md](operation-and-overrides.md) | OVR | On-device, HA and voice operation |
| [rules-groups-schedules.md](rules-groups-schedules.md) | RUL | House level, groups, windows, schedules |
| [test-strategy.md](test-strategy.md) | TST | TimeProvider, simulator, scenarios |
| [distribution.md](distribution.md) | DST | Zip release, HACS, download counting |
| [documentation.md](documentation.md) | DOC | Multilingual user documentation |
| [brand.md](brand.md) | BRD | Name, logo, colours |
| [open-questions.md](open-questions.md) | — | Open decisions, device checklist |
