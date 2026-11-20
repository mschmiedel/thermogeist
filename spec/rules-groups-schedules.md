# Rules, groups, schedules

## House level and inheritance

| ID | Requirement | Status |
|---|---|---|
| RUL-001 | Hierarchy house → group → room. Groups are free-form (e.g. floor, bedrooms). A room belongs to at most one group. | planned |
| RUL-002 | Every setting shows its effective source ("inherited from house", "set in group Bedrooms", "overridden in room"). | planned |
| RUL-003 | Central mode for the whole house: `auto` / `stop` / `frost_protection`. Survives restarts. Default `auto`. | implemented |
| RUL-004 | Frost protection setpoint 7 °C (named constant). Common TRV frost settings are 5–8 °C; 7 °C keeps a margin for poorly insulated rooms. | implemented |
| RUL-005 | Central mode `holiday`. | planned |

## Rules

| ID | Rule | Status |
|---|---|---|
| RUL-010 | Window: open for a configurable time (default 30 s) → frost protection. After closing, back with its own delay. | planned |
| RUL-011 | Away: setback, limited to max. 2 K in the heat-pump profile. | planned |
| RUL-012 | Start-up delay after an HA restart until devices are available (`startup_hold`). | planned |
| RUL-013 | Sensor failure: after a configurable time, safe state (minimum opening), always with reason code `safety_sensor_stale`. | planned |

## Schedules

| ID | Requirement | Status |
|---|---|---|
| RUL-020 | Schedules at house or group level, overridable per room. | planned |
| RUL-021 | In the heat-pump profile, changes are applied as a ramp, not a step. | planned |
| RUL-022 | Optional: use existing HA `schedule` entities as a source. | planned |

## Precedence

With several reasons active at once (highest first):

1. Safety (sensor failure, frost protection)
2. Central mode (stop, holiday)
3. Window
4. User override
5. Away
6. Schedule

| ID | Requirement | Status |
|---|---|---|
| RUL-030 | The precedence order is fixed and documented. `active_reason` shows the effective reason, other active reasons as an attribute. | planned |
