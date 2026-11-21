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
| CTL-032 | Integral part with integral time `Ti = τ`, limited to 2–24 h; without heat load `Ti = 8 h`. It integrates the true error (the dead band only calms the proportional part). With a feed-forward it only integrates within ±1 K of the target, so large steps do not wind it up; without one it always integrates. Integration stops while the output is saturated (anti-windup). Start value: 30 % without feed-forward, 0 with; the start value is removed as soon as a feed-forward arrives (and added back if it is lost), so it never counts twice. | implemented |
| CTL-033 | Output shaping in this order: limit to 0–100 %, raise to the minimum opening while heating, limit the change to `max change per 30 min` pro rata, round to 1 %. The reported position only changes by at least 1 %, so rounding never makes the valve twitch; internally the controller keeps the unrounded value. Decisions and plans are only computed after start-up, once room temperatures are read. | implemented |
| CTL-034 | Without a target (central stop) the output is 0 %. With a silent sensor (safety) the output is the minimum opening, at least 20 %. | implemented |
| CTL-035 | Every result carries its parts (feed-forward, proportional, integral), the limits applied and the reason, so users can see why the valve would move. Without a feed-forward the attribute is empty and `feed_forward_missing` names the missing inputs (heat load, radiator output, flow temperature, room temperature). | implemented |
| CTL-036 | The feed-forward inverts a typical valve characteristic: `valve = 10 % + 90 % × heat fraction²` (heat output rises steeply right after the opening point). Learned per thermostat later (LRN-003). | implemented |
| CTL-038 | The feed-forward uses the flow temperature as a 30-minute moving average, not the momentary value. Field finding: at 6–9 K between water and room, the flow dropping from 31.5 to 28 °C moved the feed-forward from 26 % to 69 % within 25 minutes; heat-pump cycling and defrosting would make the plan jump. | implemented |
| CTL-039 | Flow temperature hygiene. Recommended is a sensor in the heating circuit (after a buffer, where the radiators get their water): when it drops during hot-water charging, opening the valves a little is correct compensation. If the chosen flow sensor sits at the heat generator outlet, it shows hot-water temperatures during charging; then an optional "heat generator state" entity lets Thermogeist hold the last valid value during hot water and defrost. In every case implausible values (below room temperature, above 70 °C, jumps of several K per minute) are discarded and the last valid value is held. Visible as attribute (`flow_held`, reason). | in progress (plausibility implemented; hold via generator state planned) |
| CTL-040 | The controller state is stored and restored after a restart, so a room does not relearn for hours: the slow correction (integral), whether it still holds the start value, and the relaxed-minimum state. Saved at most once per minute (delayed write) and when Home Assistant stops. A state older than 24 h (named constant) is not restored: after a long outage the house has changed too much. The last output is not restored; the valve's reported position seeds it (CTL-044). | implemented |
| CTL-041 | Diagnostic sensors per room for feed-forward, proportional and integral part (%), disabled by default, for history graphs. | planned |
| CTL-042 | The plan is recomputed at most once per minute; a changed reason (window, stop, safety) is applied at once. Sensor noise between those minutes is ignored. | implemented |
| CTL-043 | While the room is above its target, the output never increases, whatever the feed-forward says (limit `hold_when_warm`). Field finding: a falling flow temperature pushed the plan from 30 to 54 % while the room was 0.3 K too warm. | implemented |
| CTL-044 | After a restart the controller starts from the valve position the thermostat reports (role `valve_read`), so the rate limit applies from the first step. Write-only settings (Sonoff `valve_opening_degree`) are not used as a start. Field finding: a restart made the valve jump from 30 to 54 %. | implemented |
| CTL-045 | When a room's valves change – a thermostat added, replaced or removed, or its roles or strategy edited – the stored controller state is not restored: the room starts fresh from the heat demand (feed-forward), or from a reported valve position (CTL-044). The learned correction belongs to the old valves and would otherwise hold a wrong position for hours. Detected by a key of devices, roles and strategy stored with the state; changes of the rated output do not count. Happens automatically, there is no button for it. | implemented |
| CTL-037 | Comfort beats the minimum opening: more than 0.5 K above the dead band, the valve may close below the minimum opening (limit `min_opening_relaxed`); the minimum applies again once the room is back inside the dead band. Oversized radiators then cycle slowly, the honest consequence until the sizing diagnosis exists (DIA-001). | implemented |

Room heat capacity for τ (MDL-014): 46 Wh/(m²·K) of floor area – the "medium" construction class
of EN ISO 13790 (165 kJ/(m²·K)).

## Special cases

| ID | Requirement | Status |
|---|---|---|
| CTL-020 | Cycling only as a last resort when the room is heavily oversized. Always accompanied by the diagnosis "radiator too big" (DIA-001). | planned |
| CTL-021 | Do not operate near the opening point: the minimum opening stays well above the learned opening point plus its scatter. | planned |
| CTL-023 | Minimum opening per thermostat: measured opening point + scatter + 5 % safety margin, once known from calibration (CAL-005) or learning (LRN-003). Until then the house value applies. The source ("measured" or "house value") is visible per thermostat. The house value of 40 % (heat pump) is an informed estimate, not a calculation; on the Bosch HT II, 30 % has proven safe (flow starts at 10–20 %, 20 % not guaranteed). | planned |
| CTL-022 | Always approach target positions from the same direction to avoid gear backlash. Do not readjust below the backlash size. | planned |

## Deliberately not

| ID | Approach | Status | Reason |
|---|---|---|---|
| CTL-090 | Pure on/off control | rejected | Thermogeist aims for calm rooms and quiet valves: graded valve positions keep the temperature steady, on/off makes it swing |
| CTL-091 | Full model predictive control (MPC) | rejected (for now) | Thermogeist aims for decisions users can follow; MPC is hard to explain. Possible later as an option |
