# SCN-THERMO-017: A Sonoff shows its derived valve position

**Spec:** ACT-016
**Test:** `tests/ha/test_thermostats.py::test_sonoff_shows_derived_valve_position`

## Initial state
A room with a Sonoff TRVZB, opening degree 43 %, closing degree 70 %.

## Steps
1. The Sonoff heats.
2. The Sonoff goes idle.

## Expected result
1. *Valve position* shows 43 % with `source: derived`, `hvac_action: heating`.
2. It shows 30 %.

## Why it matters
Users see whether the device really opens to the planned position or rests at the minimum.
