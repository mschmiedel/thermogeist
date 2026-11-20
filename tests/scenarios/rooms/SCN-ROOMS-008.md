# SCN-ROOMS-008: The room dialog asks for the factor of each heat source

**Spec:** MDL-040, MDL-042, MDL-044
**Test:** `tests/ha/test_heat_sources.py::test_room_dialog_asks_for_factors`

## Initial state
A house; a gaming PC power sensor reporting 300 W.

## Steps
1. Add a room with the PC as heat source and a known share.
2. In the extra step set the PC's factor to 50 %.
3. Open the room's gear icon again.

## Expected result
- The share step is not the last one; the factor step follows.
- The room stores the PC with 50 %; "Heat from devices" shows 150 W with the sources as attribute.
- The gear dialog shows the PC as chosen heat source.

## Why it matters
Users see and control which devices count, and how much.
