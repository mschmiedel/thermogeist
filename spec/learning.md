# Learning and learning state

The user can always see whether a room is still learning, has settled, or is drifting.

## What is learned

| ID | Quantity | Status |
|---|---|---|
| LRN-001 | Room heat loss H and heat capacity C (start value from the model) | planned |
| LRN-002 | Radiator effectiveness (includes presetting and hydraulics) | planned |
| LRN-003 | Valve opening point and characteristic | planned |
| LRN-004 | Gain k for setpoint modulation (ACT-011) | planned |
| LRN-005 | Heat-up rate for pre-heating | planned |
| LRN-006 | House energy signature from daily means of heat output (MDL-017), indoor and outdoor temperature; yields the measured house heat loss (W/K) and heat load at design temperature, offered as a suggestion for MDL-002. Hot water and defrost phases excluded, outlier days filtered. | planned |

## Stage 1: what a room really needs (learned demand factor)

The model (MDL-011, MDL-012, CTL-036) predicts which valve position holds a room at its target.
In the field it can be off by a factor of two (PyM: held 21.6 °C with about half the heat the
model expects – an oversized radiator with a high presetting, sun, sleeping people). Stage 1
learns one number per room from normal operation: how much of the modelled demand the room
really needs. It does not need an empty or locked room. Separating heat loss and radiator
strength (LRN-001, LRN-002) is a later stage.

| ID | Requirement | Status |
|---|---|---|
| LRN-030 | **Quiet hour.** An hour counts for learning when, for the whole hour and the hour before: no window open and no window event (RUL-010), reason `setpoint`, no sensor failure, outdoor below 15 °C, flow known (MDL-007); the room is near its target (hourly mean within ±0.3 K) and steady (change over the hour at most 0.2 K); the valve position is known for every thermostat of the room (reported or derived, ACT-016; the plan only while Thermogeist sets a valve-based thermostat). | implemented |
| LRN-031 | **Observation.** In a quiet hour the heat the room received is the estimated radiator output (MDL-013, hourly mean) plus the heat from devices (MDL-044); the room was steady, so this equals its loss. The observation is `received / modelled demand` (MDL-011 at the room temperature). Hours with a modelled demand below 50 W are left out (the ratio would be noise). | implemented |
| LRN-032 | **Learned demand factor.** The median of the observations of the last 21 days, limited to 25–300 %. At least 24 quiet hours on at least 3 different days are needed; until then the room shows `learning` with progress (LRN-013). A median is used because single disturbed hours (visitors, cooking, a door left open) must not move it. | implemented |
| LRN-033 | **Day and night.** Observations are tagged night (22–6 h) or day. If both have at least 12 quiet hours and their medians differ by more than 25 %, each period uses its own factor (bedroom with sleeping people, a room with sun or devices in the day); otherwise one factor for both. | implemented |
| LRN-034 | **Use.** Once a factor is valid, the feed-forward uses `modelled demand × factor` (CTL-030); the change reaches the valve through the normal rate limit, so it never jumps. The slow correction (integral) then has less to do. Every change of more than 10 percentage points is written to the logbook. | implemented |
| LRN-035 | **Visible.** Room sensor "Learned demand" (%, 100 % = as the model says) with attributes: `state` (`learning` / `settled` / `not_assessable`), `quiet_hours`, `days`, `night_pct`, `day_pct`, `spread_pct`. The docs explain it as "this room needs about X % of what its inputs suggest" and what typically causes a big deviation (oversized radiator, wrong share of the heat load, sun, people). | implemented |
| LRN-036 | **Reset.** Changing the room's heat-load inputs or its thermostats (CTL-045) clears its observations; so does a button "Learning: start again" on the room. Observations survive restarts (stored like the heating curve, DIA-013). | implemented |
| LRN-037 | **Limits stated.** In rooms whose thermostats report their valve late (Bosch Smart Home, see OVR-006) the observations are rough; the room shows `spread_pct` and needs more hours before it is `settled`. | implemented |

## Visibility

| ID | Entity / display | Status |
|---|---|---|
| LRN-010 | `learning_state`: `learning` / `settled` / `drifting` / `not_assessable` | planned |
| LRN-011 | `calibration_change_24h`: change of learned values within 24 h, with a threshold for "significant jump" | planned |
| LRN-012 | `model_deviation`: deviation of learned vs. expected from the inputs | planned |
| LRN-013 | Progress when data is insufficient, e.g. "3 of 5 cold days" | planned |

## Rules

| ID | Requirement | Status |
|---|---|---|
| LRN-020 | Learning only happens in steady phases (no open window, no ramp, no override). Phases with an open door are learned separately or left out (OPN-010). | planned |
| LRN-023 | Learning pauses automatically when the room warms clearly faster than radiator and known heat sources explain ("unexplained heat", e.g. a LAN party in a small room), when the central mode is stop, or within one hour after a manual change. The pause reason is shown. | planned |
| LRN-024 | Per room a switch "Learning" to pause by hand, optionally for a duration (e.g. 24 h for a party weekend). Control keeps running; only adapting the learned values pauses. | planned |
| LRN-025 | Every change of the learning state (learning / paused with reason / settled / drifting) appears in the logbook. | planned |
| LRN-021 | Learning can be paused and reset per room. Both produce a reason code. | planned |
| LRN-022 | All learning steps are deterministically testable via `TimeProvider` and the simulator. | planned |
