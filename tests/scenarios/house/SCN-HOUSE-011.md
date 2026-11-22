# SCN-HOUSE-011: A heating curve from two points

**Spec:** MDL-019
**Test:** `tests/core/test_house.py::test_heating_curve_from_two_points`

## Initial state
A curve with the cold point −10 °C → 45 °C and the warm point 15 °C → 30 °C.

## Steps
1. Read the flow temperature at −10, 5 and 15 °C outside.
2. Read it at −20 and 20 °C outside.

## Expected result
1. 45 °C, 36 °C (on the straight line) and 30 °C.
2. 45 °C and 30 °C: beyond the points the curve stays flat.
3. The house with this curve is valid.

## Why it matters
Heat generators hold their limits beyond the set points; a straight line extended forever would
promise flow temperatures the heat generator never delivers.
