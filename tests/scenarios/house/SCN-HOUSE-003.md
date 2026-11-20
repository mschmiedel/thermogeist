# SCN-HOUSE-003: Values just inside the limits are accepted, values just outside are rejected

**Spec:** MDL-002, MDL-003, MDL-009, MDL-016
**Test:** `tests/core/test_house.py::test_limits_are_checked_at_both_edges`

## Initial state
A minimal house as in SCN-HOUSE-001.

## Steps
For each optional value, validate once at the limit and once just beyond it:
- heat load 0.5 / 100 kW vs. 0.4 / 100.1 kW (with design temperature −12 °C)
- design outdoor temperature −40 / +10 °C vs. −40.1 / +10.1 °C
- share outside 0 / 100 % vs. −0.1 / 100.1 %
- living area 10 / 10 000 m² vs. 9.9 / 10 000.1 m²

## Expected result
- Values at the limits: no issues.
- Values beyond: exactly one issue with the code `<field>_out_of_range` on that field.

## Why it matters
Typos like 80 instead of 8 kW are caught at input instead of producing a strange controller later.
