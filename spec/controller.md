# Controller

## Structure

```
Room model ──► Feed-forward ─┐
                             ├─► Heat demand 0–100 % ─► Limiters/overrides ─► Output shaping ─► Adapter
Actual temp ─► Feedback ─────┘
```

| ID | Block | Requirement | Status |
|---|---|---|---|
| CTL-001 | Feed-forward | Expected heat demand from the room model (MDL-013). Skipped without model data. | planned |
| CTL-002 | Feedback | Slow PI controller on room temperature with anti-windup. The integral term is the learned correction. | planned |
| CTL-003 | Limiters | Frost protection, over-temperature, sensor failure, window. Every intervention produces a reason code. | planned |
| CTL-004 | Output shaping | Minimum/maximum opening, dead band, rate limit, adaptation to the device's resolution. | planned |
| CTL-005 | Controller speed | Integral time derived from the room time constant τ. | planned |

## Profiles by heating type

| ID | Profile | Behaviour | Status |
|---|---|---|---|
| CTL-010 | Heat pump ("limiter") | high minimum opening (default 40 %), dead band up to setpoint + 0.5 K, max. 10 % valve change per 30 min, setback max. 2 K with ramp | planned |
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
