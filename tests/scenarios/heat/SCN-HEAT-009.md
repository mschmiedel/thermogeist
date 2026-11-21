# SCN-HEAT-009: House demand and supply cover the same rooms

**Spec:** MDL-052 to MDL-054
**Test:** `tests/core/test_output.py::test_house_balance_covers_the_same_rooms`

## Initial state
Three rooms: A (demand 300 W, radiators 250 W, devices 100 W), B (demand 200 W, radiators
150 W, no devices), C (demand 400 W, no radiator estimate).

## Steps
1. Build the house balance.

## Expected result
- Demand 500 W, radiators 400 W, devices 100 W, over 2 rooms.
- C is named as room without estimate and left out of all three sums.

## Why it matters
A demand over all rooms against radiators over some of them would look like a deficit that
does not exist.
