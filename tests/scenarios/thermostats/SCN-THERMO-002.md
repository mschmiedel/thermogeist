# SCN-THERMO-002: Bosch: actual valve position next to the planned one

**Spec:** ACT-015, ACT-120
**Test:** `tests/ha/test_thermostats.py::test_bosch_shows_actual_next_to_planned`

## Initial state
As SCN-THERMO-001, but a Bosch BTH-RA "Bath TRV" with pi_heating_demand at 39 %.

## Steps
1. Assign without radiator output.
2. The device reports 45 %.

## Expected result
- Valve position sensor shows 39 %, then 45 %.
- Without radiator output the planned position shows `feed_forward: null` and `feed_forward_missing: [radiator_output]`.

## Why it matters
You can compare your current regulation with Thermogeist before letting it control anything.
