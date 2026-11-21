# SCN-SIZING-002: The heating curve is learned from the hours while heating ran

**Spec:** DIA-014
**Test:** `tests/core/test_sizing.py::test_heating_curve_is_learned_carefully`

## Initial state
Hourly values of a heat pump whose flow follows `35 °C − 0.6 · outdoor`.

## Steps
1. Fit with 47 hours, with 48 hours over only 4 K of outdoor temperature, with 48 hours over
   10 K (2 °C to 12 °C), and with a line that rises with the outdoor temperature.
2. Ask the learned line for the design day (−10.5 °C) and for −20 °C.

## Expected result
- Not learned with 47 hours, with less than 5 K span and with a rising line.
- Learned: 41.3 °C at −10.5 °C; confidence *medium* (12.5 K below the coldest hour), *low* at
  −20 °C, *high* at 0 °C.
- An hour counts only when the flow is at least 5 K above the mean room temperature.

## Why it matters
The design-day flow is extrapolated; Thermogeist must say how far it trusts it and must not guess
from a single mild day.
