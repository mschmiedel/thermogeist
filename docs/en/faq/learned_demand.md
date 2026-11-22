# Learned demand

**English** | [Deutsch](../../de/faq/learned_demand.md)

## What you see

Room sensor **Learned demand** in %, with the attributes `state` (`learning` / `settled`),
`quiet_hours`, `days`, `day_pct`, `night_pct` and `spread_pct`.

## What it means

From your inputs – heat load, the room's share, radiator output – Thermogeist works out how
much heat a room needs. Real rooms differ. Thermogeist therefore watches **quiet hours** of
normal operation: window closed (also in the hour before), the room steady at its target, the
valve position known. In such an hour, the heat the room received from its radiators and
devices is exactly what it lost.

*Learned demand* is the result: **the room needs about this share of what its inputs
suggest.** 100 % means the inputs fit. 50 % means half the expected heat is enough.

- You do not have to do anything: no empty or locked room, no test run.
- It needs at least 24 quiet hours on 3 days, usually 3–5 nights. Until then the state is
  `learning`.
- It uses the median of the last 21 days, so a single evening with visitors or the oven on does
  not change it.
- If day and night differ clearly (more than 25 %), each gets its own value (`day_pct`,
  `night_pct`): a bedroom with sleeping people needs less at night, a sunny room less by day.
- Once valid, Thermogeist uses it to plan the valve. The change reaches the valve slowly, like
  every other change. Big changes appear in the logbook.

## Why a room is far from 100 %

| Learned demand | Typical causes |
|---|---|
| clearly below 100 % | radiator larger or stronger than entered (high presetting), the room's share of the heat load set too high, sun, people, devices without a power sensor, a warm neighbouring room |
| clearly above 100 % | radiator weaker than entered (presetting too low, air, covered), share set too low, a cold neighbouring room or stairwell |

It is not a fault. If a value seems implausible, check the inputs of the room.

## Limits

Thermostats that report their valve position late (Bosch Smart Home) make the observations
rough; `spread_pct` is then larger and it takes longer until the value settles.

## What to do

- Nothing. To start again (e.g. after a renovation), press **Learning: start again** on the
  room. Changing the room's heat-load inputs or its thermostats starts learning again by itself.
