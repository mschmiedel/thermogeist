# SCN-HEAT-005: Heat from devices reduces what the radiator has to deliver

**Spec:** MDL-042, MDL-043
**Test:** `tests/core/test_heat.py::test_heat_sources_reduce_the_demand`

## Initial state
A PC at 300 W (factor 100 %), a washing machine at 2000 W (factor 10 %), one unavailable and one
negative power sensor.

## Steps
1. Sum the heat from the sources.
2. Subtract it from a demand of 800 W, 400 W and an unknown demand.

## Expected result
- 500 W from devices; unavailable and negative readings count as 0 W.
- 300 W, 0 W (never negative) and unknown remain for the radiator.

## Why it matters
A room warmed by devices must not get the full radiator heat on top.
