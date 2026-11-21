# SCN-SIZING-007: Oversized radiators: reserve for heat pumps, hints for boilers and the house

**Spec:** DIA-010, DIA-011, DIA-013
**Test:** `tests/ha/test_sizing.py::test_oversized_rooms`

## Initial state
A house with 3 kW heat load, two rooms with a 10 000 W radiator each and a learned heating
curve.

## Steps
1. Start as a heat-pump house.
2. Start as a boiler house.

## Expected result
1. Both rooms `heavily_oversized`, `note: reserve`, `cause: flow_high`; no room repair issue; the
   house issue *flow probably higher than needed* exists.
2. Room repair issues *radiator heavily oversized* for both rooms and the house issue.

## Why it matters
With a heat pump a large radiator is welcome; that all rooms are oversized says the flow
temperature could be lower, which saves energy.
