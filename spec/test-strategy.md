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
| TST-012 | Device models for the adapters (Sonoff, Bosch) including their behaviour on failure. | planned |
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
