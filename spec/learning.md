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
| LRN-021 | Learning can be paused and reset per room. Both produce a reason code. | planned |
| LRN-022 | All learning steps are deterministically testable via `TimeProvider` and the simulator. | planned |
