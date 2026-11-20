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
| MDL-004 | Room share of the heat load in % | room | recommended | planned |
| MDL-005 | Room floor area and height | room | optional | rejected (replaced by MDL-033) |
| MDL-006 | Radiator: rated output (W at 75/65/20) or type + dimensions | radiator | optional | planned |
| MDL-007 | Flow temperature: sensor entity or heating curve as two points | house | optional | planned |
| MDL-008 | Outdoor temperature: sensor entity with device class temperature (e.g. weather station, heat pump outdoor sensor) | house | yes | implemented |
| MDL-009 | Share of the heat load outside Thermogeist in %, 0–100 (rooms it does not control, e.g. a bathroom with floor heating). Default 0 %. | house | optional | implemented |
| MDL-016 | Heated living area in m², 10–10 000. Only used to suggest MDL-009 from the area not covered by rooms (suggestion follows in M2). | house | optional | implemented |
| MDL-017 | Heat output of the heat generator: sensor entity (W), plus an indicator for domestic hot water and defrost phases so they can be excluded. Measurement only, never controlled. | house | optional | planned |

The room share in % is the default rather than W/m² because it also works with differing room
heights and exterior wall shares.

## Room share: three ways in

The share already contains ceiling height, slopes and exposure. The question is only how the user
gets to it.

| ID | Requirement | Status |
|---|---|---|
| MDL-030 | **Known:** the user enters the room's value from a room-by-room heat load calculation (EN 12831), as % or W. Most accurate. | planned |
| MDL-031 | **Estimated (default):** Thermogeist estimates a weight from geometry and position (MDL-033) and distributes the house heat load by weight. | planned |
| MDL-032 | **Learned:** learning (LRN-001) measures the real heat loss per room and shows the deviation from the entered or estimated share (LRN-012). The input stays the starting point; a good start means less to learn. | planned |
| MDL-033 | Geometry and position per room: floor area; ceiling height, or lowest and highest point for sloped ceilings (mean height is used); number of exterior walls (0–3); what is above (heated / unheated / roof) and below (heated / unheated / ground). Galleries and open spaces count their floor area once with the full height. | planned |
| MDL-034 | The weighting is simple and explainable: its factors are named constants documented in this spec. The UI shows the result ("Living room: estimated 31 % ≈ 2.5 kW"), and the user can accept or override it. | planned |
| MDL-035 | Estimated weights are distributed over the share Thermogeist controls: 100 % minus MDL-009. Known shares (MDL-030) are taken as entered; estimated rooms share the rest. | planned |
| MDL-036 | Without a house heat load, weights still give relative shares; absolute watts are missing and the controller starts cautiously (MDL-020). | planned |

The weighting factors for MDL-034 are defined when M2 is built and recorded here.

## Derived quantities

| ID | Quantity | Formula / derivation | Status |
|---|---|---|---|
| MDL-010 | Room heat loss coefficient H (W/K) | `P_room / (T_set − T_design)` with `P_room = heat load · share` | planned |
| MDL-011 | Current demand (W) | `H · (T_set − T_outdoor)` | planned |
| MDL-012 | Available radiator output (W) | rated output · (ΔT_log / 49.8)^n, n ≈ 1.3 (EN 442) | planned |
| MDL-013 | Expected heat demand | demand / available output | planned |
| MDL-014 | Time constant τ = C / H | C estimated from room volume and construction | planned |
| MDL-015 | Oversizing factor | available output at design temperature / demand | planned |

## Without inputs

| ID | Requirement | Status |
|---|---|---|
| MDL-020 | If heat load or radiator data are missing, the controller runs feedback-only with cautious defaults. The UI shows which features are unavailable as a result. | planned |
| MDL-021 | Room shares plus the share outside Thermogeist (MDL-009) add up to at most 100 %. Above that, setup shows an error; below 100 % is shown as a hint ("12 % of the heat load is not assigned to any room"). | planned |
