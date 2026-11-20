# Controller

## Structure

```
Room model ──► Feed-forward ─┐
                             ├─► Heat demand 0–100 % ─► Limiters/overrides ─► Output shaping ─► Adapter
Actual temp ─► Feedback ─────┘
```

| ID | Block | Requirement | Status |
|---|---|---|---|
| CTL-001 | Feed-forward | Expected heat demand from the room model (MDL-013). Skipped without model data. | implemented |
| CTL-002 | Feedback | Slow PI controller on room temperature with anti-windup. The integral term is the learned correction. | implemented |
| CTL-003 | Limiters | Frost protection, over-temperature, sensor failure, window. Every intervention produces a reason code. | planned |
| CTL-004 | Output shaping | Minimum/maximum opening, dead band, rate limit, adaptation to the device's resolution. | implemented |
| CTL-005 | Controller speed | Integral time derived from the room time constant τ. | implemented |

## Profiles by heating type

| ID | Profile | Behaviour | Status |
|---|---|---|---|
| CTL-010 | Heat pump ("limiter") | high minimum opening (default 40 %), dead band up to setpoint + 0.5 K, max. 10 % valve change per 30 min, setback max. 2 K with ramp | implemented |
| CTL-011 | Fossil ("comfort") | faster feedback, setback allowed, pre-heating with learned heat-up rate | planned |
| CTL-012 | Direct electric ("switching") | time-proportional cycling with long cycles | planned |

All profile values are defaults and can be overridden per house, group or room.

### Profile default values

Provisional until the controller is tuned with the simulator (M3). Shown on the house device so
users can see what their heating type implies.

| Parameter | Heat pump | Boiler | Direct electric | Why |
|---|---|---|---|---|
| Minimum valve opening | 40 % | 0 % | 0 % | Heat pumps need flow; boilers and electric heaters may close fully |
| Dead band above setpoint | 0.5 K | 0.2 K | 0.2 K | Heat pump: ignore small overshoots instead of closing |
| Max. valve change per 30 min | 10 % | 30 % | 100 % | Heat pump: slow and calm; electric: cycling needs full steps |
| Max. setback | 2 K | 4 K | 4 K | Heat pump: deep setbacks cost more to recover than they save |

| ID | Requirement | Status |
|---|---|---|
| CTL-013 | The profile for a heating type provides the default values above. | implemented |
| CTL-014 | The four values are editable on the house device (number entities, category configuration). A changed value overrides the profile until reset; attribute `source` shows `profile` or `user`. A button resets all four to the profile. Changing the heating type keeps user values; untouched values follow the new profile. Allowed ranges: minimum opening 0–100 %, dead band 0–2 K, max. change 1–100 % per 30 min, max. setback 0–6 K. | implemented |

## Controller details (M3)

Runs every minute per room, deterministic via `TimeProvider`.

| ID | Requirement | Status |
|---|---|---|
| CTL-030 | Feed-forward `u_ff = demand / available radiator output × 100 %` (MDL-011, MDL-012). Without heat load, radiator output or flow temperature it is 0 and feedback alone does the work. | implemented |
| CTL-031 | Proportional part `Kp × e` with `Kp = 15 %/K`. The error `e = target − room temperature`; overshoot inside the dead band counts as 0. | implemented |
| CTL-032 | Integral part with integral time `Ti = τ`, limited to 2–24 h; without heat load `Ti = 8 h`. It integrates the true error (the dead band only calms the proportional part). With a feed-forward it only integrates within ±1 K of the target, so large steps do not wind it up; without one it always integrates. Integration stops while the output is saturated (anti-windup). Start value: 30 % without feed-forward, 0 with. | implemented |
| CTL-033 | Output shaping in this order: limit to 0–100 %, raise to the minimum opening while heating, limit the change to `max change per 30 min` pro rata, round to 1 %. The reported position only changes by at least 1 %, so rounding never makes the valve twitch; internally the controller keeps the unrounded value. Plans are only computed after start-up, once room temperatures are read. | implemented |
| CTL-034 | Without a target (central stop) the output is 0 %. With a silent sensor (safety) the output is the minimum opening, at least 20 %. | implemented |
| CTL-035 | Every result carries its parts (feed-forward, proportional, integral), the limits applied and the reason, so users can see why the valve would move. | implemented |
| CTL-036 | The feed-forward inverts a typical valve characteristic: `valve = 10 % + 90 % × heat fraction²` (heat output rises steeply right after the opening point). Learned per thermostat later (LRN-003). | implemented |
| CTL-037 | Comfort beats the minimum opening: more than 0.5 K above the dead band, the valve may close below the minimum opening (limit `min_opening_relaxed`); the minimum applies again once the room is back inside the dead band. Oversized radiators then cycle slowly, the honest consequence until the sizing diagnosis exists (DIA-001). | implemented |

Room heat capacity for τ (MDL-014): 46 Wh/(m²·K) of floor area – the "medium" construction class
of EN ISO 13790 (165 kJ/(m²·K)).

## Special cases

| ID | Requirement | Status |
|---|---|---|
| CTL-020 | Cycling only as a last resort when the room is heavily oversized. Always accompanied by the diagnosis "radiator too big" (DIA-001). | planned |
| CTL-021 | Do not operate near the opening point: the minimum opening stays well above the learned opening point plus its scatter. | planned |
| CTL-022 | Always approach target positions from the same direction to avoid gear backlash. Do not readjust below the backlash size. | planned |

## Deliberately not

| ID | Approach | Status | Reason |
|---|---|---|---|
| CTL-090 | Pure on/off control | rejected | too aggressive, root of the original problem |
| CTL-091 | Full model predictive control (MPC) | rejected (for now) | hard to explain, too much for the start; possible later as an option |
