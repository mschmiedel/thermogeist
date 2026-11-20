# SCN-ROOM-004: Design indoor temperature is checked in both share modes

**Spec:** MDL-039
**Test:** `tests/core/test_room.py::test_design_indoor_temperature_is_checked_in_both_modes`

## Initial state
An estimated room and a room with known share.

## Steps
1. Validate with 24 °C.
2. Validate with 35 °C and 9 °C.

## Expected result
- 1: valid.
- 2: `design_indoor_temperature_out_of_range`.

## Why it matters
Typos are caught; 10–30 °C covers halls to bathrooms.
