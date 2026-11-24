# Test strategy

## TimeProvider

Domain logic never reads the clock directly. It receives a `TimeProvider`.

| ID | Requirement | Status |
|---|---|---|
| TST-001 | `TimeProvider` provides `now()` (timezone-aware, UTC) and `monotonic()` (seconds). | implemented |
| TST-002 | `SystemTimeProvider` for production, `FakeTimeProvider` for tests and the simulator. | implemented |
| TST-003 | `FakeTimeProvider` can be advanced deliberately (`advance`) but never moved backwards. Naive timestamps are rejected. | implemented |
| TST-004 | The HA layer passes the `SystemTimeProvider` to the core. No core module creates one itself. | planned |

## Room simulator

| ID | Requirement | Status |
|---|---|---|
| TST-010 | Thermal room model (H, C, radiator per EN 442, outdoor temperature, disturbances such as window and sun), one-minute steps. Lives in `tests/sim/`. | implemented |
| TST-011 | Valve model with opening point and a concave characteristic (heat output rises steeply after the opening point). Scatter and backlash later. | implemented |
| TST-012 | Device models of thermostats that regulate themselves, fitted to field data and kept in `tests/sim/devices.py`: Bosch Radiator Thermostat II (BTH-RA, integrating: opens 2.9 % per K and minute, closes 7.5 %, plus 5 % per K of error change) and Bosch Smart Home thermostat, first generation (proportional band 30 % per K around a valve that moves between days, never below 23 %, corrections of 10 % or more at most every 20 minutes, own window function closing at a 1 K drop). One or two recorded days per device live in `tests/fixtures/devices/` (relative time, no dates or room names); a test checks that each model reproduces them within 4 % on average. Sonoff valves are written directly (no own regulation to model); their failure behaviour is covered by DIA-024. | implemented |
| TST-015 | Closed loop for the setpoint strategy (`tests/sim/setpoint_run.py`): simulated room, a device model and Thermogeist's setpoint logic (ACT-051 to ACT-053, offset average over 30 minutes), one-minute steps. | implemented |
| TST-013 | Simulated weeks run in seconds, driven by `FakeTimeProvider`. | implemented |
| TST-014 | Hydraulic network for balancing (DIA-033). | planned |

## Test scenarios

| ID | Requirement | Status |
|---|---|---|
| TST-020 | Every meaningful scenario has a file in `tests/scenarios/<feature>/` with ID, initial state, steps and expected result. | implemented |
| TST-021 | The matching test names the scenario ID in its docstring. A meta test checks that every scenario ID has a test and vice versa. | implemented |

## Control quality metrics

For comparisons (between profiles, devices or versions):

- overshoot above setpoint (K)
- time to setpoint ± 0.3 K after a setpoint step
- standard deviation around setpoint in steady phases
- valve movements per day and total travel
- average valve opening (house level, heat-pump profile)

| ID | Requirement | Status |
|---|---|---|
| TST-030 | A test helper computes these metrics from a simulator run so controller tests can assert on them. | implemented |
