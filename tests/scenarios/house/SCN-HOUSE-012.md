# SCN-HOUSE-012: An implausible heating curve is rejected

**Spec:** MDL-019
**Test:** `tests/core/test_house.py::test_implausible_heating_curve_is_rejected`

## Initial state
A valid curve −10 °C → 45 °C, 15 °C → 30 °C.

## Steps
1. Make the warm point as cold as the cold point.
2. Make the flow at the warm point higher than at the cold point.
3. Enter a flow of 95 °C.

## Expected result
1. `curve_warm_not_above_cold` on the warm outdoor field.
2. `curve_flow_rises_when_warmer` on the warm flow field.
3. `curve_cold_flow_out_of_range`.

## Why it matters
Swapped points are an easy typo; they would turn the curve upside down without anyone noticing.
