# SCN-HEAT-007: Output follows the assumed valve characteristic

**Spec:** MDL-013, CTL-036
**Test:** `tests/core/test_output.py::test_output_follows_the_valve_characteristic`

## Initial state
A radiator that gives 400 W fully open at the current temperatures.

## Steps
1. Estimate the output at valve 5 %, 10 %, 55 % and 100 %.

## Expected result
- 5 % and 10 %: 0 W (below the opening point no water flows).
- 55 %: about 283 W (half the valve range gives about 71 % of the heat).
- 100 %: 400 W.
- Estimating the output at the valve the feed-forward plans for a demand gives back that demand.

## Why it matters
The estimate uses the same characteristic as the valve planning, only in the other direction;
both must agree.
