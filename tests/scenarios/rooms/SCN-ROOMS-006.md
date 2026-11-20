# SCN-ROOMS-006: Changing a room recalculates its share

**Spec:** HAI-005
**Test:** `tests/ha/test_rooms.py::test_reconfigure_room`

## Initial state
Room "Living room" with 20 m² in a 160 m² house.

## Steps
1. Reconfigure the room to 40 m².

## Expected result
- Share 25 %.

## Why it matters
Corrections are easy and take effect immediately.
