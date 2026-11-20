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
| RUL-010 | Window: rooms may have window contacts (binary sensors, optional). Any contact open for 30 s → reason `window_open`, target frost protection, valve 0 % at once (no rate limit). Closed again → back to the previous valve position without slow ramp-up. Delays configurable with RUL-014, frost guard with RUL-015. | implemented |
| RUL-014 | Window delays: *close after* (window open this long → valve closes, default 30 s) and *resume after* (all contacts closed this long → back to normal, default 10 s). The resume delay bridges switching from fully open to tilted, which passes through "closed" for a moment; a contact re-opening during it keeps the valve closed. Both are number entities (0–600 s): on the house as control settings (reset with the house's reset button), and on every room with window contacts, where they show the house value until changed (attribute `source`: house or room); a room button puts them back to the house value. Replaces the fixed 30 s / 0 s of RUL-010. | implemented |
| RUL-015 | Frost guard while a window is open: if the room falls below the frost protection setpoint (RUL-004, 7 °C), the room is heated towards it although the window is open; above 8 °C (1 K hysteresis, named constant) the valve closes again. Setpoint thermostats get 7 °C instead of 5 °C while the guard is active. Visible as reason parameter `frost_guard` on `window_open` and in the logbook. | implemented |
| RUL-011 | Away: setback, limited to max. 2 K in the heat-pump profile. | planned |
| RUL-012 | Start-up delay after an HA restart until devices are available (`startup_hold`). | implemented |
| RUL-013 | Sensor failure: if the room temperature sensor has not reported a valid value for 60 min (named constant; configurable later), the room's reason is `safety_sensor_stale`. A sensor that is unavailable at start-up gets the full 60 min grace period. From M4 the safe state is the minimum opening. | implemented |

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
| RUL-030 | The precedence order is fixed and documented. `active_reason` shows the effective reason. Other active reasons as an attribute follow later. | implemented |
