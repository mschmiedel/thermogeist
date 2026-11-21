# Radiator size

**English** | [Deutsch](../../de/faq/radiator_sizing.md)

## What you see

The room sensor **Radiator size** (in the room's diagnostic section) with one of these values,
and possibly a repair issue under **Settings → Repairs**:

| Value | Meaning |
|---|---|
| Much larger than needed | Even on the coldest design day the room needs less than 30 % of what its radiators deliver. |
| Right size | 30–90 %. |
| Just enough | 90–100 %: on the coldest days there is hardly any reserve. |
| Too small | Over 100 %, or the valve stayed wide open on cold days and the room still did not get warm. |
| Not assessable yet | Something is missing; the attribute `missing` says what. |

## How Thermogeist works it out

1. **Demand on the design day:** heat loss of the room (from its share of the heat load) times
   the difference between your setpoint and the design outdoor temperature.
2. **Flow on the design day:** Thermogeist learns your heating curve. Every hour while heating
   runs, it notes the outdoor temperature and the flow temperature (the median, so hot water
   bursts do not count). From 48 hours over at least 5 K of outdoor temperature it draws a
   straight line and extends it to the design day. The house sensor **Flow on the design day**
   shows the result; `confidence` says how far the line had to be extended (*high* up to 5 K
   below the coldest hour seen, *medium* up to 15 K, else *low*). In early autumn it takes a few
   days until the line is learned.
3. **Radiator output on that day** from the rated output of the room's thermostats (EN 442).
4. **In operation:** an hour counts as "fully open in the cold" when the valve was at least 95 %
   open, the room more than 0.5 K below its target and it was below 5 °C outside. Six such hours
   within a week mean *too small*, whatever the calculation says. In observe mode this needs a
   thermostat that reports its valve position.

Devices that heat the room are not counted: you cannot rely on them on the coldest day.

The attributes show the numbers: `load_pct`, `factor` (output / demand), `design_flow_c`,
`design_demand_w`, `design_output_w`, `full_open_hours`, `basis` (`static` = calculated,
`operation` = observed) and `cause`.

## Too small

`cause: radiator_small` – the radiators deliver too little at the learned flow temperature.

- Is the rated output of the thermostats right (at 75/65/20 °C, from the data sheet)?
- Is the room's share of the heat load plausible? A room open to a neighbouring room (wide door,
  open plan) gets heat from there; describe both as one room with all their thermostats.
- Options: a larger or additional radiator, a higher heating curve (costs efficiency with a heat
  pump), or accepting a little less on the coldest days.

`cause: input_or_hydraulics` – the calculation says it is fine, but in operation the room does not
get warm with the valve wide open.

- Is the radiator covered (curtain, furniture, cladding)?
- Is the presetting of the valve insert too closed, or is the radiator not hydraulically
  balanced? Is there air in it?
- Is the rated output entered too high?

## Much larger than needed

- **Heat pump:** no fault. A large radiator lets the heat pump run with a low flow temperature,
  which saves energy (attribute `note: reserve`, no repair issue).
- **Boiler or direct electric:** the valve mostly works almost closed, which makes control less
  fine. Closing the presetting of the valve insert a little helps.
- **All rooms much larger than needed** (`cause: flow_high`, repair issue *flow temperature
  probably higher than needed*): the heating curve is probably set higher than your house needs.
  Lowering it step by step saves energy, especially with a heat pump. Thermogeist does not change
  your heating system; do it on the heat pump or boiler and watch the rooms for a few days.

## Not assessable yet

`missing` names what is missing: `heat_load` (heat load and design outdoor temperature on the
house), `radiator_output` (rated output of the thermostats), `flow_temperature` (flow sensor on
the house) or `heating_curve` (not enough heating hours learned yet – wait a few days).
