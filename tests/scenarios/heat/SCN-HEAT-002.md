# SCN-HEAT-002: Without heat load there are no absolute watts

**Spec:** MDL-036
**Test:** `tests/core/test_heat.py::test_no_heat_load_gives_no_watts`

## Initial state
House without heat load.

## Steps
1. Calculate heat loss and demand.

## Expected result
- Both are unknown (None), no error.

## Why it matters
Thermogeist works without a heat load; it only cannot show watts.
