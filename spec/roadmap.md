# Roadmap

Order of delivery. Each milestone is usable on its own and builds on the previous one. Details
live in the feature specs; this file only says *what comes when*. A milestone is done when all
listed requirements are `implemented`.

The MVP is milestones 1–4: describe the house, add rooms, watch what Thermogeist would do, then
let it control one thermostat type.

## M0 – Foundation (done)

Repository, spec structure, `TimeProvider`, scenario tests, architecture guards, zip build,
brand.

## M1 – House (done)

The user installs Thermogeist and describes the house once.

| Scope | Requirements |
|---|---|
| Config flow creates one house: name, heating type, outdoor temperature sensor | MDL-001, MDL-008, HAI-001, HAI-002 |
| Optional: heat load and design outdoor temperature (with suggestion) | MDL-002, MDL-003 |
| Optional: share outside Thermogeist, heated living area as helper | MDL-009, MDL-016 |
| Options flow to change everything later | HAI-003 |
| House device in HA with the effective settings as diagnostic entities | HAI-004 |
| Central mode for the house: auto / stop / frost protection | RUL-003 |
| Profile defaults derived from the heating type | CTL-010, CTL-011, CTL-012 (defaults only) |
| Getting-started docs en/de | DOC-001 to DOC-003 |

## M2 – Rooms (done)

The user adds rooms to the house. Thermogeist knows each room's need, but controls nothing yet.

| Scope | Requirements |
|---|---|
| Rooms as sub-entries of the house: name, HA area, temperature sensor | MDL-004, HAI-005 |
| Room share known or estimated from geometry and position, distributed over the controlled share | MDL-030, MDL-031, MDL-033 to MDL-036 |
| Derived values: heat loss coefficient, current demand | MDL-010, MDL-011 |
| Plausibility: room shares add up to at most 100 %, missing inputs explained | MDL-020, MDL-021 |
| Per room: setpoint, `active_reason` | OVR-012, RSN-002 |
| Decision point and reason catalogue (first codes: `setpoint`, `central_stop`, `frost_protection`, `safety_sensor_stale`) | ARC-003, RSN-001, RSN-005, RUL-030 |
| Editable control settings on the house, icons | CTL-014, HAI-013 |
| Sensor failure handling for the room temperature | RUL-013 |

## M3 – Thermostats, observe mode (done)

Thermostats are assigned to rooms. Thermogeist calculates what it *would* do and shows it,
without writing to the devices.

| Scope | Requirements |
|---|---|
| Assign thermostats to rooms: roles, kinds, device profiles | ACT-001 to ACT-009, ACT-020, ACT-021, ACT-030 to ACT-033, HAI-006 |
| Radiator output and flow temperature (optional) | MDL-006, MDL-007, MDL-012, MDL-014 |
| Controller: feed-forward, feedback, output shaping, heat-pump profile | CTL-001, CTL-002, CTL-004, CTL-005, CTL-010, CTL-030 to CTL-035 |
| Observe mode: planned valve position and reason per room, actual position per thermostat, nothing is written | ACT-014, ACT-015 |
| Room simulator for controller tests | TST-010, TST-011, TST-013 |
| Control quality metrics in tests | TST-030 |

## M4 – Thermostats, control (MVP complete, done)

Thermogeist controls Sonoff TRVZB thermostats.

| Scope | Requirements |
|---|---|
| Control switch per room; direct valve control for valve-based thermostats (Bosch BTH-RA first, Sonoff TRVZB/TRV-ZBT), device setup and restore, write verification | ACT-008, ACT-010, ACT-040 to ACT-045, ACT-100 to ACT-103, ACT-120, ACT-121 |
| Switch per room between observe and control | ACT-014 |
| Window rule, delays, frost guard | RUL-010, RUL-014, RUL-015 |
| Manual change on the thermostat or in HA becomes an override | OVR-001 to OVR-004, OVR-010, OVR-011 |
| Start-up delay after HA restart | RUL-012 |
| Logbook entries and repair issues | RSN-003, RSN-004 |
| Device docs and FAQ for all reason codes en/de | DOC-004 |

## M5 – Beta

Thermogeist can be recommended to others. Features are not a criterion: versions stay 0.x until
the planned features are in, then 1.0 marks feature completeness. The beta is about trust.

| Scope | Requirements |
|---|---|
| No breaking change without migration: every change of stored settings comes with a config entry migration and a test; renamed entities keep their unique ids | to be specified |
| Name check before the first beta (see `open-questions.md`) | – |
| Setup dialogs never lose entered data on cancel | HAI-021 |
| Minimum firmware from the profile, warning on older firmware | ACT-017, ACT-105 |
| Every reason code and diagnosis has an FAQ page; install via HACS and zip documented | DOC-004, DST-005 |
| Spec statuses honest: product goals and old placeholders reviewed (PRD-001 to PRD-007, CTL-003, TST-004), open questions up to date | – |

## After the MVP (order to be decided)

- Schedules and away mode (RUL-011, RUL-020 to RUL-022)
- Groups and inheritance (RUL-001, RUL-002, ARC-005)
- Learning and learning state (LRN-*): stage 1, the learned demand factor per room with day/night (LRN-030 to LRN-037), done; open: heat loss and radiator strength separately (LRN-001, LRN-002), valve characteristic (LRN-003), learning state details (LRN-010 to LRN-013, LRN-020 to LRN-025), energy signature (LRN-006)
- Radiator sizing diagnostics: static and operation check, learned heating curve (MDL-015, DIA-001 to DIA-005, DIA-010 to DIA-015, DIA-023), lost calibration reported by the device (DIA-024) done; open: empirical extrapolation (DIA-006), DIA-020 to DIA-022, a valve that does not open without a device report (DIA-025)
- Calibration mode (CAL-*)
- Bosch BTH-RA and Sonoff TRV-ZBT adapters (ACT-110, ACT-120 to ACT-124)
- Generic `climate` adapter (ACT-011, ACT-012, ACT-130)
- Fossil and electric profiles beyond defaults (CTL-011, CTL-012)
- Hydraulic balancing (DIA-030 to DIA-033)
- Flow temperature: return sensor and heating curve fallback (MDL-019) done; open: hold during hot water and defrost via the heat generator state (CTL-039)
- Diagnostic sensors for the controller parts (CTL-041); controller state across restarts (CTL-040) done
- **Internal heat sources** (gaming PC, server, aquarium …) from power sensors (MDL-040, MDL-042 to MDL-044, MDL-048, MDL-049 done); open: pre-fill from the room's area (MDL-041, with HAI-007), learning (MDL-045), fixed-power switch (MDL-047)
- Openings and neighbouring zones: doors to unheated halls, door sensors, separate learning (OPN-*)
- Usability of the setup: dialogs that show only what is needed (HAI-016, HAI-018 to HAI-021: questions in the house dialog, collapsible sections, detected roles collapsed, thermostats offered when adding a room) done; open: diagrams in the docs; done before: room coverage (MDL-046), thermostats inside their room (HAI-007), flow/return/spread on the house (DIA-042)
- Combination of heaters and thermostats in one room (ACT-068)
- Heaters with stages (ACT-060 to ACT-067, ACT-069) done; wood stove as disturbance (MDL-050); hybrid heat generators (MDL-051, later)
- Heat output of the heat generator: energy signature, measured heat load, house balance (MDL-017, LRN-006, DIA-040, DIA-041)
- Suggested heating curve from the learned demand of the rooms, a suggestion only, never written to the heat generator (DIA-050 to DIA-056)
- Smart child lock per room, adopted from the device, set again after a reset, 30 minutes off for a battery change (OVR-022 to OVR-024) done; open: per group (OVR-020)
