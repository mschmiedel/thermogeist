# Diagnostics

## Radiator sizing per room

Two sources that check each other:

1. **Static** from inputs: available radiator output / room demand (MDL-015).
2. **Empirical** from operation: average opening in steady phases plotted against outdoor
   temperature and extrapolated to the design temperature. This source takes precedence.

| ID | Classification | Criterion (initial value) | Status |
|---|---|---|---|
| DIA-001 | heavily oversized | demand at design temperature < 30 % | planned |
| DIA-002 | right size | 30–90 % | planned |
| DIA-003 | tight | 90–100 % | planned |
| DIA-004 | undersized | > 100 %, or permanently 100 % in cold weather without reaching setpoint | planned |
| DIA-005 | not assessable | fewer than 5 steady days below 5 °C | planned |

| ID | Requirement | Status |
|---|---|---|
| DIA-010 | The message depends on the profile. With a heat pump, oversizing is a reserve, not a fault. | planned |
| DIA-011 | If all rooms are oversized, a house-level hint follows (flow temperature probably higher than needed), without touching the heating system. | planned |
| DIA-012 | Sensor `<room>_sizing` with factor, confidence, data basis and probable cause. | planned |
| DIA-013 | Actionable cases as an HA repair issue with a link to the FAQ entry. | planned |

## House balance

| ID | Requirement | Status |
|---|---|---|
| DIA-040 | Compare measured house heat output (MDL-017) with the sum of learned room losses plus the share outside Thermogeist. Show how much of the heat the room models explain, and hint when MDL-009 looks wrong. | planned |
| DIA-041 | Heat output clearly above room demand while rooms stay cold points to losses outside the rooms (e.g. pipes in an unheated basement). | planned |
| DIA-042 | The heating water is visible on the house device: flow, return and spread as sensors, showing the averaged values the controller actually uses (not the raw sensors), with the source entity as attribute. | planned |

## Distinguishing causes

| ID | Data | Probable cause | Status |
|---|---|---|---|
| DIA-020 | Valve 100 %, room cold, other rooms fine | presetting too closed, hydraulics | planned |
| DIA-021 | Valve 100 %, pipe stays cold (calibration probe) | air, stuck valve pin, TRV not opening | planned |
| DIA-022 | One room needs a lot, others little | uneven distribution | planned |
| DIA-023 | Statically fine, empirically too small | wrong input, radiator covered | planned |

## Hydraulic balancing (staged)

| ID | Stage | Status |
|---|---|---|
| DIA-030 | Stage 1: identify the critical room, relative suggestions for presettings, applied manually. Refers to professional balancing (procedure B). | planned |
| DIA-031 | Stage 2: automatic limit on maximum opening during heat-up so all rooms arrive at the same time. | planned |
| DIA-032 | Stage 3: continuous dynamic balancing via a slow house loop (days). Only after stages 1 and 2 have proven themselves. | planned |
| DIA-033 | Stages 2 and 3 require a hydraulic network in the simulator (pump, pipes, valves). | planned |
