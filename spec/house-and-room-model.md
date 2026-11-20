# House and room model

The model provides starting values, controller tuning and plausibility checks. It is not fixed
truth: learning corrects it (see [learning.md](learning.md)).

## Inputs

| ID | Input | Level | Required | Status |
|---|---|---|---|---|
| MDL-001 | Heating type: `heat_pump` / `boiler` (gas, oil, pellets, district heating) / `direct_electric` | house (room can override later) | yes | implemented |
| MDL-002 | House heat load in kW at design outdoor temperature, 0.5–100 kW | house | recommended | implemented |
| MDL-003 | Design outdoor temperature in °C, −40 to +10 °C. Entered by the user; required when a heat load is given. Help text points to the heat load calculation or a public lookup by postcode. | house | recommended | implemented |
| MDL-018 | Look up the design outdoor temperature from the HA location using a table, not an estimate. Open: a data source that may be redistributed under MIT (the DIN/TS 12831-1 table may not; candidate: computed from open DWD climate data). | house | optional | planned |
| MDL-004 | Room share of the heat load in % | room | recommended | implemented |
| MDL-005 | Room floor area and height | room | optional | rejected (replaced by MDL-033) |
| MDL-006 | Radiator rated output in W at 75/65/20 °C, per thermostat (type + dimensions later) | thermostat | optional | implemented |
| MDL-007 | Flow temperature: sensor entity (heating curve as two points later) | house | optional | implemented |
| MDL-019 | Heating curve as two points as a fallback when no flow sensor exists (planned). Optional return temperature sensor (implemented): the measured system spread (flow − return, 30-minute average, limited to 1–10 K) replaces the assumed 5 K, i.e. mean radiator water = flow − spread / 2. The house return is the mixed return of all radiators, so it is used for the spread only, not as the return of a single radiator. | house | optional | in progress |
| MDL-008 | Outdoor temperature: sensor entity with device class temperature (e.g. weather station, heat pump outdoor sensor) | house | yes | implemented |
| MDL-009 | Share of the heat load outside Thermogeist in %, 0–100 (rooms it does not control, e.g. a bathroom with floor heating). Only needed when the value is known from a heat load calculation; otherwise it follows from MDL-016 as the part not covered by rooms. Default 0 %. | house | optional | implemented |
| MDL-016 | Heated living area in m², 10–10 000. Reference for estimating room shares (MDL-031): a room's share starts at its floor area divided by the living area. Input implemented; used from M2. | house | recommended | implemented |
| MDL-017 | Heat output of the heat generator: sensor entity (W), plus an indicator for domestic hot water and defrost phases so they can be excluded. Measurement only, never controlled. | house | optional | planned |

The room share in % is the default rather than W/m² because it also works with differing room
heights and exterior wall shares.

## Room share: three ways in

The share already contains ceiling height, slopes and exposure. The question is only how the user
gets to it.

| ID | Requirement | Status |
|---|---|---|
| MDL-030 | **Known:** the user enters the room's value from a room-by-room heat load calculation (EN 12831), as % or W. Most accurate. | implemented |
| MDL-031 | **Estimated (default):** a room's share = its floor area / heated living area (MDL-016), adjusted by a weight from height and position (MDL-033). Each room can be estimated on its own, before all rooms are entered. | implemented |
| MDL-032 | **Learned:** learning (LRN-001) measures the real heat loss per room and shows the deviation from the entered or estimated share (LRN-012). The input stays the starting point; a good start means less to learn. | planned |
| MDL-033 | Geometry and position per room: floor area; ceiling height, or lowest and highest point for sloped ceilings (mean height is used); number of exterior walls (0–3); what is above (heated / unheated / roof) and below (heated / unheated / ground). Galleries and open spaces count their floor area once with the full height. | implemented |
| MDL-034 | The weighting is simple and explainable: its factors are named constants documented in this spec. The UI shows the result ("Living room: estimated 31 % ≈ 2.5 kW"), and the user can accept or override it. | implemented |
| MDL-035 | The part of the heat load not covered by any room is shown on the house ("18 % not assigned to a room"). If MDL-009 is entered, the difference to it is shown as a plausibility hint. Without a living area, estimated rooms share 100 % minus MDL-009 by weight (fallback). | implemented |
| MDL-036 | Without a house heat load, weights still give relative shares; absolute watts are missing and the controller starts cautiously (MDL-020). | implemented |
| MDL-037 | Halls, corridors and stairwells: without a thermostat they may be left out (their part stays "not assigned") or entered as rooms without a thermostat to complete the house balance (DIA-040) and to act as neighbouring zone for doors (OPN-002). With a thermostat they are normal rooms; few exterior walls give them a small weight. | implemented |
| MDL-038 | The heated living area excludes balconies and terraces, even though residential floor area rules count them partly. | implemented |
| MDL-039 | Design indoor temperature per room (default 20 °C, 10–30 °C; EN 12831: bathrooms 24 °C, heated halls 15 °C). Planning value only: it scales the estimated share by `(T_design_in − T_design_out) / (20 − T_design_out)` (only when the design outdoor temperature is known) and is the indoor value for the heat loss coefficient (MDL-010). How warm the room is heated is decided by the setpoint alone. | implemented |

### Weighting factors (MDL-034)

`share = 100 % × floor area × height factor × exposure factor / heated living area`

| Factor | Value | Why |
|---|---|---|
| Height factor | `0.5 + 0.5 × mean height / 2.5 m`, plus 0.05 per metre above 3 m | About half of a room's loss scales with height (walls, air volume), half does not (floor, ceiling). Warm air collects under high ceilings. |
| Exposure base | 0.6 | An interior room still loses heat through ventilation and to colder neighbours. |
| Per exterior wall | +0.2 | Outside walls and windows are the main loss. |
| Above: unheated / roof | +0.15 / +0.3 | A roof loses more than a ceiling to an unheated attic. |
| Below: unheated / ground | +0.15 / +0.1 | Ground is milder than an unheated basement. |

A typical room (2.5 m, two exterior walls, heated above and below) has both factors at 1.0, so
its share equals its share of the living area. If the estimated shares exceed what is
available (100 % minus share outside minus known shares), they are scaled down together and
the room sensor shows `scaled_down: true`. Values are provisional; learning (MDL-032) corrects
them.

## Internal heat sources

Electrical devices turn almost all their power into heat in the room. A gaming PC with 300 W can
cover a whole room's demand (observed in a basement room: demand 270 W, valve at 24 %, room
above setpoint). Without knowing this, the feed-forward plans far too much and the integral
corrects only after hours – and again in the other direction when the device is switched off.

| ID | Requirement | Status |
|---|---|---|
| MDL-040 | Rooms may list heat sources: power sensors (W) of devices in the room, optional, changeable later via the room's gear icon. | planned |
| MDL-041 | If the room has an HA area, power sensors in that area are pre-filled as suggestions; the user keeps only what really heats the room. Later: hint when a new power sensor appears in the area. | planned |
| MDL-042 | Per heat source a factor 0–100 % (default 100 %) for devices that release only part of their power into the room (e.g. a vented dryer). | planned |
| MDL-043 | The feed-forward uses `demand − heat from sources`, never below 0. When a source switches off, the feed-forward rises at once without waiting for the integral. | planned |
| MDL-044 | Per room a sensor "Heat from devices" (W); the planned valve position shows how much of the demand the sources cover. | planned |
| MDL-045 | Learning (LRN-001) accounts for known heat sources so they do not distort the learned heat loss. | planned |

## Derived quantities

| ID | Quantity | Formula / derivation | Status |
|---|---|---|---|
| MDL-010 | Room heat loss coefficient H (W/K) | `P_room / (T_design_in − T_design_out)` with `P_room = heat load · share`, `T_design_in` from MDL-039 | implemented |
| MDL-011 | Current demand (W) | `H · (T_set − T_outdoor)` | implemented |
| MDL-012 | Available radiator output (W) | rated output · (ΔT / 49.8 K)^1.3 (EN 442), with `ΔT = flow − 2.5 K − room` (half of a typical 5 K spread); 0 if ΔT ≤ 0 | implemented |
| MDL-013 | Expected heat demand | demand / available output | planned |
| MDL-014 | Time constant τ = C / H | C estimated from room volume and construction | implemented |
| MDL-015 | Oversizing factor | available output at design temperature / demand | planned |

## Without inputs

| ID | Requirement | Status |
|---|---|---|
| MDL-020 | If heat load or radiator data are missing, the controller runs feedback-only with cautious defaults. The UI shows which features are unavailable as a result. | planned |
| MDL-021 | Known room shares plus the share outside Thermogeist (MDL-009) add up to at most 100 %; above that, the room dialog shows an error. Below 100 % is shown on the house as "heat load not assigned to a room". | implemented |
